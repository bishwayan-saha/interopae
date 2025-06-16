import json
import logging
import os
from typing import List

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters
from sub_agents.smart_response_agent.agent import create_smart_response_agent

from utils.customer_session_manager import CustomMCPToolset as MCPToolset

load_dotenv()

logger = logging.getLogger(__name__)


def get_indian_railway_tools():
    toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "mcp-remote", "https://railway-mcp.amithv.xyz/mcp"],
        )
    )
    return toolset


def create_railway_agent():
    toolset = get_indian_railway_tools()

    return LlmAgent(
        name="railway_agent",
        model="gemini-2.0-flash-exp",
        description="The transportation agent has access to different tools like Indian railway ",
        instruction="""
            # 🛤️ System Prompt: Rail Info Agent (MCP-Enhanced)

            You are a smart assistant specialized in retrieving Indian Railways information using MCP tools.  
            Given user inputs like source, destination, date of journey, train number, or station code, your task is to:

            ## 🎯 Core Responsibilities
            1. **Understand the user query** – Determine whether the user wants:
            - Train list
            - Seat availability
            - Fare
            - Train schedule
            - Live running status
            2. **Map query to MCP-compatible format** – Extract relevant parameters and prepare a structured request.
            3. **Invoke MCP rail tool** – Use the MCP tool to search and retrieve accurate rail information.
            4. **Present smart results** – Return clean, structured, and user-friendly responses including:
            - Train name & number
            - Departure & arrival times
            - Seat availability (with class)
            - Fare details
            - Running status or delays
            5. **Assist further** – Suggest next actions like:
            - "Want to check fare details?"
            - "Should I look for alternate trains?"
            - "Would you like to see seat availability?"

            ## 🧠 Behavior Rules
            - ❌ Never hallucinate or fabricate rail data.
            - ✅ Use only the MCP tool for all rail-related queries.
            - ⚠️ Clearly notify the user if required inputs are missing (e.g., station code not recognized).
            - 🧾 Prioritize actionable and summarized output over verbose explanations.
        """,
        tools=[toolset],
        output_key="railway_agent"
    )

def create_transportation_agent():
    return SequentialAgent(
        name="transportation_agent",
        description=""" 
        The transportation agent has access to different tools like Indian railway and 
        uses the smart_response_agent to provide resoureful response
    """,
    sub_agents=[create_railway_agent(), create_smart_response_agent()],
)

root_agent = create_transportation_agent()



