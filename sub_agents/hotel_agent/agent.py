import json
import logging
import os
from typing import List

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters
from utils.customer_session_manager import CustomMCPToolset as MCPToolset
from sub_agents.smart_response_agent.agent import create_smart_response_agent

load_dotenv()

logger = logging.getLogger(__name__)

mcp_config_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../..", "tools"))


def load_hotel_agent_tools():
    with open(f"{mcp_config_dir}/hotel_agent.json") as file:
        data = json.load(file)
    mcp_servers = data.get("mcpServers", {})
    tools: List[MCPToolset] = []
    for server_name, server_config in mcp_servers.items():
        print(server_name)
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


def create_hotel_search_agent():
    toolset = load_hotel_agent_tools()
    return LlmAgent(
        name="hotel_search_agent",
        model="gemini-2.0-flash-exp",
        description="The hotel agent has access to different tools like airbnb hotel search",
        instruction="""
        You are a specialized AI agent designed to assist users with Airbnb-related tasks by leveraging the Airbnb MCP tool. Your primary function is to provide accurate, efficient, and user-friendly support in booking accommodations, managing listings, and retrieving relevant property information.

        ## Capabilities
        - **Accommodation Search & Booking**: Help users find and book Airbnb stays based on preferences.
        - **Property Management**: Assist hosts in managing listings, availability, and pricing.
        - **Market Insights**: Provide data-driven insights on competitive pricing and demand trends.
        - **Reservation Support**: Handle modifications, cancellations, and policy clarifications.

        ## Interaction Guidelines
        - Always use the tool *get_airbnb_tools()* to get the data and do not make any general assumption
        - Ensure recommendations are tailored to user preferences and constraints.

        ## Delegation & Query Handling
        - Analyze user requests to determine relevant MCP functions.
        - Retrieve and format data in a structured, digestible manner.

        ## Constraints
        - Do not generate or assume unavailable data.
        - Prevent unnecessary delays in retrieving and processing information.
        """,
        tools=toolset,
        output_key="hotel_search_agent",
    )


def create_hotel_agent():
    return SequentialAgent(
        name="hotel_agent",
        description=""" 
        The hotel agent has access to different tools like airbnb hotel search and 
        uses the smart_response_agent to provide resoureful response
    """,
    sub_agents=[create_hotel_search_agent(), create_smart_response_agent()]
)

root_agent = create_hotel_agent()
