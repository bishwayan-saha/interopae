import asyncio
import json
import logging

import mcp.server.stdio
import requests
from dotenv import load_dotenv
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type
from mcp import types as mcp_types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

load_dotenv()

logger = logging.getLogger(__name__)


def get_html_ui_code_from_deepsite(prompt: str):
    """
    Asynchronously fetches code generation output from the DeepSite API.
    Args:
        prompt (str): The user-provided prompt to generate frontend code.
    Returns:
        str: The response text from the DeepSite API.
    Raises:
        Exception: Logs an error if the request fails.
    Notes:
        - Uses an HF token from environment variables for authentication.
        - Sends a JSON payload with the prompt and provider information.
        - Implements a timeout of 150 seconds to handle API latency.
    """

    url = "https://enzostvs-deepsite.hf.space/api/ask-ai"
    headers = {
        "Cookie": "hf_token=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",
        "Content-Type": "application/json",
    }
    data = {
        "prompt": prompt,
        "provider": "auto",
        "model": "deepseek-ai/DeepSeek-V3-0324",
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=150)
    except Exception as e:
        logger.error(f"Error occurred while fetching deepsite agent \n Reason {e}")
        return {"success": False, "message": f"Error executing deepsite{str(e)}"}
    return {"success": True, "message": response.text}


app = Server("deepsite_mcp_server")

ADK_DEEPSITE_TOOLS = {
    "get_html_ui_code_from_deepsite": FunctionTool(func=get_html_ui_code_from_deepsite)
}


@app.list_tools()
async def list_mcp_tools() -> list[mcp_types.Tool]:
    mcp_tools_list = []
    for tool_name, adk_tool_instance in ADK_DEEPSITE_TOOLS.items():
        if not adk_tool_instance.name:
            adk_tool_instance.name = tool_name

        mcp_tool_schema = adk_to_mcp_tool_type(adk_tool_instance)
        mcp_tools_list.append(mcp_tool_schema)
    return mcp_tools_list


@app.call_tool()
async def call_mcp_tool(name: str, arg: dict) -> list[mcp_types.TextContent]:
    if name in ADK_DEEPSITE_TOOLS:
        adk_tool_instance = ADK_DEEPSITE_TOOLS[name]
        try:
            adk_tool_response = await adk_tool_instance.run_async(
                args=arg, tool_context=None
            )
            response_text = json.dumps(adk_tool_response, indent=2)
            return [mcp_types.TextContent(type="text", text=response_text)]
        except Exception as ex:
            error_payload = {
                "success": False,
                "message": f"Failed to execute tool '{name}': {str(ex)}",
            }
            error_text = json.dumps(error_payload, indent=2)
            return [mcp_types.TextContent(type="text", text=error_text)]
    else:
        error_payload = {
            "success": False,
            "message": f"Tool '{name}' not implemented by this server.",
        }
        error_text = json.dumps(error_payload, indent=2)
        return [mcp_types.TextContent(type="text", text=error_text)]


async def run_mcp_stdio_server():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(run_mcp_stdio_server())
    except Exception as ex:
        logger.error(
            f"MCP Server (stdio) encountered an unhandled error: {e}", exc_info=True
        )  #
