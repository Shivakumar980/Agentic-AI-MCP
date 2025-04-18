import os
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("tavily_search")

# Tavily API details
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

async def search_tavily(query: str) -> dict:
    """Performs a Tavily web search and returns 5 results."""
    if not TAVILY_API_KEY:
        return {"error": "Tavily API key is missing. Set it in your .env file."}

    payload = {
        "query": query,
        "topic": "general",
        "search_depth": "basic",
        "chunks_per_source": 3,
        "max_results": 5,  # Fixed 
        "time_range": None,
        "days": 3,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [],
        "exclude_domains": []
    }

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TAVILY_SEARCH_URL, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_tavily_results(query: str):
    """Fetches Tavily search results for a given query."""
    results = await search_tavily(query)

    if isinstance(results, dict):
        return {"results": results.get("results", [])}  # Ensure always returning a dictionary
    else:
        return {"error": "Unexpected Tavily response format"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
