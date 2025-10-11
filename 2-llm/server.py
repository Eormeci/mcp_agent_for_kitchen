from mcp.server.fastmcp import FastMCP
import asyncio
from serpapi import GoogleSearch
from typing import Optional
from pydantic import BaseModel
import json
import logging

# Logger tanımı (kullanıldığı için ekledim)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("FlightSearchService", host="localhost", port=3001)

# Pydantic Models
class FlightInfo(BaseModel):
    airline: str
    price: str
    duration: str
    stops: str
    departure: str
    arrival: str


async def run_search(params):
    """Run SerpAPI search asynchronously"""
    try:
        logger.debug(f"Sending SerpAPI request with params: {json.dumps(params, indent=2)}")
        result = await asyncio.to_thread(lambda: GoogleSearch(params).get_dict())
        logger.debug(f"SerpAPI response received, keys: {list(result.keys())}")
        return result
    except Exception as e:
        logger.exception(f"SerpAPI search error: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def search_flights(origin: str, destination: str, outbound_date: str, return_date: Optional[str] = None):
    # Prepare search parameters
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "departure_id": origin.strip().upper(),
        "arrival_id": destination.strip().upper(),
        "outbound_date": outbound_date,
        "currency": "USD",
        "type": "2"
    }

    search_results = await run_search(params)
    return search_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MCP Flight Search Service")
    parser.add_argument("--connection_type", type=str, default="http", choices=["http", "stdio"])
    args = parser.parse_args()

    server_type = "sse" if args.connection_type == "http" else "stdio"
    print(f"Starting Flight Search Service on port 3001 with {args.connection_type} connection")

    mcp.run(server_type)
