## Agentic-AI-MCP
an Agentic AI personal assistant built on LangGraph that connectsvia MCP to the tools like web research, database operations, and multimedia analysis in one conversational interface. Uses modular MCP architecture to intelligently route requests and maintain context throughout discussions.
![image](https://github.com/user-attachments/assets/738e1b20-d8b8-46aa-8613-f6220dd350fc)


## 🚀 Features

- **YouTube Video Transcipts** - Extract and chat with the content of youtube videos
- **Web Research** - Search and retrieve information from the web using Tavily API
- **Database Operations with SQLlite** - Create tables, store data, and query information with natural language
- **Weather Information** - Get real-time weather data for any location
- **Conversation Memory** - Maintains context throughout interactions

## 📋 Prerequisites

- Python 3.9+
- An OpenAI API key
- A Tavily API key (for web search functionality)

## 🔧 Installation

1. Clone the repository:
```bash
git clone  https://github.com/Shivakumar980/Agentic-AI-MCP
cd langgraph-mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## 💻 Usage

### Starting the Application

1. Start the weather server in one terminal:
```bash
python servers/weather.py
```

2. In another terminal, start the main agent:
```bash
python agent.py
```

3. Enter your queries and commands in the interactive chat interface.

### Example Commands

Here are some examples of what you can do with KnowledgeForge:

#### Web Search
```
Tell me about Aravind Srinivasan
```

#### YouTube Transcripts
```
Summarize this YouTube video:https://www.youtube.com/watch?v=SP7Ua8FKZN4
```

#### Database Operations
```
Create a table called books with columns id, title, author, and genre
```

```
Add a book with title "Dune", author "Frank Herbert", and genre "Science Fiction"
```

```
Query the books table and show me all science fiction books
```

```
Update the book Dune to set its genre to "Sci-Fi Classic"
```

#### Weather Information
```
What's the weather like in San Francisco today?
```

## 🏗️ Architecture
The agentic application uses the Model Context Protocol (MCP) to connect a LangGraph agent with several specialized servers:

1. **Tavily Server** - Handles web search requests
2. **YouTube Transcript Server** - Extracts and processes video content
4. **Weather Server** - Provides weather data
5. **Database Server** - Manages SQLite database operations

The central agent routes requests to the appropriate servers and maintains conversation context.

## 📁 Project Structure

```
langgraph-mcp/
├── agent.py                 # Main agent with chat interface
├── requirements.txt         # Project dependencies
├── agent_database.db        # SQLite database file (created automatically)
├── .env                     # Environment variables for API keys
├── README.md                # This documentation
└── servers/                 # Directory containing MCP servers
    ├── tavily.py            # Web search server
    ├── yt_transcript.py     # YouTube transcript server
    ├── weather.py           # Weather information server
    └── database.py          # SQLite database server
```

## 🙏 Acknowledgements

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) and [Model Context Protocol](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp)
- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Web search powered by [Tavily](https://tavily.com/)
