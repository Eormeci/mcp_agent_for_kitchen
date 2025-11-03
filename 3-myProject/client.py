import asyncio
import os
import sys
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow.react_agent import ReActAgent
from llama_index.llms.ollama import Ollama
from prompt_templates import DB_INSIGHT_PROMPT
from fastapi import FastAPI, Request
import uvicorn

# Configuration variables
MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3002/sse")
MODEL_NAME = os.environ.get("LLM_MODEL", "gemma3:4b")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.1"))

app = FastAPI()
agent = None  # global agent objesi


async def setup_agent():
    """Setup and return the SQLite database assistant agent"""
    print(f"Connecting to MCP server at {MCP_URL}")
    mcp_client = BasicMCPClient(MCP_URL)

    tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
    print(f"Found {len(tools)} tools")

    llm = Ollama(
        model=MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        request_timeout=120,
        temperature=TEMPERATURE
    )

    system_prompt = DB_INSIGHT_PROMPT.template.replace("{tools}", "").replace("{tool_names}", "").replace("{input}", "")
    agent_instance = ReActAgent(
        name="SQLiteAgent",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        temperature=TEMPERATURE
    )
    return agent_instance


@app.on_event("startup")
async def startup_event():
    """Initialize the agent when FastAPI starts"""
    global agent
    agent = await setup_agent()
    print("✅ Agent initialized and ready to receive requests!")


@app.post("/query")
async def handle_query(request: Request):
    """Endpoint to process database queries"""
    data = await request.json()
    user_query = data.get("query")

    if not user_query:
        return {"error": "Missing 'query' field in JSON body"}

    print(f"🧠 Processing query: {user_query}")
    try:
        response = await agent.run(user_query)
        return {"response": str(response)}
    except Exception as e:
        return {"error": str(e)}


async def cli_mode():
    """Run in CLI interactive mode"""
    print("\n🗄️ SQLite Database Assistant (CLI Mode) 🗄️")
    agent_instance = await setup_agent()
    while True:
        user_query = input("\n🔍 Your query: ")
        if user_query.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        response = await agent_instance.run(user_query)
        print(f"\n{response}")


if __name__ == "__main__":
    mode = os.environ.get("MODE", "api")  # "cli" or "api"
    if mode == "cli":
        asyncio.run(cli_mode())
    else:
        uvicorn.run("client:app", host="0.0.0.0", port=8080)
