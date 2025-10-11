import asyncio
import os
import sys
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow.react_agent import ReActAgent
from llama_index.llms.ollama import Ollama
from prompt_templates import DB_INSIGHT_PROMPT

# Configuration variables
MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3002/sse")
MODEL_NAME = os.environ.get("LLM_MODEL", "gemma3:4b")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.1"))

async def setup_agent():
    """Setup and return the SQLite database assistant agent"""
    try:
        print(f"Connecting to MCP server at {MCP_URL}")
        mcp_client = BasicMCPClient(MCP_URL)
        
        # Get tools list
        print("Fetching available tools...")
        tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
        print(f"Found {len(tools)} tools")
        for i, tool in enumerate(tools):
            print(f"  Tool {i+1}: {tool.metadata.name}")
        
        # Initialize Ollama LLM
        print(f"Initializing Ollama with model {MODEL_NAME}...")
        llm = Ollama(
            model=MODEL_NAME,
            base_url=OLLAMA_BASE_URL, 
            request_timeout=120,
            temperature=TEMPERATURE
        )
        
        # Create agent with database insight prompt
        system_prompt = DB_INSIGHT_PROMPT.template.replace("{tools}", "").replace("{tool_names}", "").replace("{input}", "")
        agent = ReActAgent(
            name="SQLiteAgent", 
            llm=llm, 
            tools=tools,
            system_prompt=system_prompt,
            temperature=TEMPERATURE
        )
        
        return agent
    except Exception as e:
        print(f"Error setting up agent: {str(e)}")
        raise

async def main():
    """Main function to run the SQLite database assistant"""
    print("\n🗄️ SQLite Database Assistant 🗄️")
    print("-" * 50)
    
    print("Make sure the MCP SQLite server is running with:")
    print("python mcp_sqlite_reader.py --connection_type http --port 3002")
    
    try:
        # Set up the agent
        agent = await setup_agent()
        print("Ready to query databases!")
        
        # Start conversation loop
        while True:
            user_query = input("\n🔍 Your query: ")
            
            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\nThank you for using the SQLite Database Assistant. Goodbye!")
                break
            
            if user_query.strip():
                print("Processing query...")
                try:
                    response = await agent.run(user_query)
                    print(f"\n{response}")
                except Exception as e:
                    print(f"Error processing query: {e}")
                
    except Exception as e:
        print(f"Error: {e}")
        print(f"Make sure the MCP server is running at {MCP_URL}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))