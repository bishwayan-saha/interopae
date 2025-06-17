import json
import logging
import os
from typing import List

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters

from utils.customer_session_manager import CustomMCPToolset as MCPToolset

load_dotenv()

logger = logging.getLogger(__name__)

mcp_config_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../..", "tools"))


def load_travel_agent_tools():
    with open(
        f"{mcp_config_dir}/{os.path.basename(os.path.dirname(__file__))}.json"
    ) as file:
        data = json.load(file)
    mcp_servers = data.get("mcpServers", {})
    tools: List[MCPToolset] = []
    for server_name, server_config in mcp_servers.items():
        toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command=server_config.get("command"),
                args=server_config.get("args"),
            )
        )
        tools.append(toolset)
    return tools


# def get_airbnb_tools():
#     toolset = MCPToolset(
#         connection_params=StdioServerParameters(
#             command="npx",
#             args=["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
#         )
#     )
#     return toolset


def create_hotel_agent():
    toolset = load_travel_agent_tools()

    return LlmAgent(
        name="hotel_agent",
        model="gemini-2.0-flash-exp",
        description="The hotel agent has access to different tools like airbnb hotel search",
        instruction="""
                Your AI agent designed to assist users with hotel searching. 
                your primary function is to provide accurate, efficient, and user-friendly 
                support in booking accommodations, managing listings, and retrieving relevant property information.
                ## Capabilities
                - Search/book stays
                - Manage listings & pricing
                - Share market insights
                - Support reservations & policies
                ## Guidelines
                - Use `load_travel_agent_tools()` only — no assumptions
                - Personalize responses
                - Confirm critical details
                ## Constraints
                - No made-up data
                - Follow Airbnb policies
                - Minimize delays
        """,
        tools=toolset,
        output_key="hotel_agent",
    )


root_agent = create_hotel_agent()
