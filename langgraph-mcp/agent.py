import asyncio
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent")

# Define llm
logger.info("Initializing ChatOpenAI model")
model = ChatOpenAI(model="gpt-4o")

# MCP server configuration
MCP_SERVERS = {
    "tavily": {
        "command": "python",
        "args": ["servers/tavily.py"],
        "transport": "stdio",
    },
    "youtube_transcript": {
        "command": "python",
        "args": ["servers/yt_transcript.py"],
        "transport": "stdio",
    }, 
    "math": {
        "command": "python",
        "args": ["servers/math.py"],
        "transport": "stdio",
    },       
    "weather": {
        "url": "http://localhost:8000/sse", # start your weather server on port 8000
        "transport": "sse",
    },
    "database": {
        "command": "python",
        "args": ["servers/database.py"],
        "transport": "stdio",
    }
}

async def process_message(message, conversation_history):
    """Process a single message using the agent."""
    async with MultiServerMCPClient(MCP_SERVERS) as client:
        # Load available tools
        logger.info("Loading available tools from MCP servers")
        tools = client.get_tools()
        
        # Create the agent
        logger.info("Creating agent")
        agent = create_react_agent(model, tools)
        
        # Include the new message
        current_messages = conversation_history + [HumanMessage(content=message)]
        
        # Process the query
        logger.info(f"Processing query: {message}")
        agent_response = await agent.ainvoke({"messages": current_messages})
        
        # Get the latest response
        latest_response = agent_response["messages"][-1].content
        
        return latest_response

async def main():
    """Run the interactive chat loop."""
    # Create the system message with comprehensive instructions
    system_message = SystemMessage(content=(
        "You have access to multiple tools that can help answer queries. "
        "Use them dynamically and efficiently based on the user's request. "
        "\n\nYou can use the database tools to store and retrieve persistent information: "
        "\n- Key-Value operations: store_value, get_value, list_keys"
        "\n- Notes operations: add_note, get_note, search_notes"
        "\n- Table operations: create_table, list_tables, describe_table, insert_record, query_table, delete_table"
        "\n- Record operations: update_record, delete_records"
        "\n\nFor custom tables, you can:"
        "\n1. Create tables with create_table(table_name, schema)"
        "\n2. Insert data with insert_record(table_name, fields, values)"
        "\n3. Query data with query_table(table_name, conditions, limit)"
        "\n4. Update data with update_record(table_name, set_clause, where_clause)"
        "\n5. Delete records with delete_records(table_name, where_clause)"
        "\n\nYou are a helpful knowledge assistant. Maintain context across the conversation."
    ))
    
    # Initialize conversation history
    conversation_history = [system_message]
    
    print("\nKnowledge Assistant with Database (type 'exit' to quit)\n")
    print("Assistant: Hello! I'm your knowledge assistant with database capabilities. How can I help you today?")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check if user wants to exit
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\nAssistant: Goodbye! Have a great day!")
            break
        
        # Process the message
        response = await process_message(user_input, conversation_history)
        
        # Add the exchange to conversation history
        conversation_history.append(HumanMessage(content=user_input))
        conversation_history.append(AIMessage(content=response))
        
        # Print the response
        print(f"\nAssistant: {response}")
        
        # Keep conversation history at a reasonable length
        if len(conversation_history) > 10:  # Max 10 messages including system message
            conversation_history = [system_message] + conversation_history[-9:]

# Run the chat interface
if __name__ == "__main__":
    logger.info("Starting interactive chat agent")
    asyncio.run(main())