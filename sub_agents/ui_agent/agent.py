import os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters

from utils.customer_session_manager import CustomMCPToolset as MCPToolset

base_dir = os.path.dirname(os.path.abspath(__file__))


def get_ui_html_deepsite_tool():
    toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command="python3",
            args=[f"{base_dir}/server.py"],
        )
    )
    return toolset


def create_ui_deepsite_agent():
    return LlmAgent(
        name="ui_agent",
        model="gemini-2.0-flash-exp",
        description="The travel agent has access to different tools like airbnb hotel search",
        instruction="""
                        Website UI Generator using DeepSite API
                        Your task is to generate frontend code by calling the **`get_ui_html_deepsite_tool`** tool.
                        #### **Steps:**
                        1. **Identify Intent:** Ensure the request is related to UI or website design.
                        2. **Extract User Prompt:** Use the user’s input to determine the request.
                        3. **Generate Output:** Retrieve **HTML code only** from the tool.
                        4. **Mandatory Tool Call:** You **MUST** invoke `get_ui_html_deepsite_tool`.  
                        - **Do NOT** generate code manually.  
                        - **Do NOT** hallucinate responses.     
                        Always rely on the tool for accurate code generation.    
                    """,
        tools=[get_ui_html_deepsite_tool()],
        output_key="ui_agent",
    )


root_agent = create_ui_deepsite_agent()
