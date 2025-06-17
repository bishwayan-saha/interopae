from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent

from sub_agents.hotel_agent.agent import create_hotel_agent
from sub_agents.ui_agent.agent import create_ui_deepsite_agent

load_dotenv()


def create_manager_agent():
    hotel_agent = create_hotel_agent()
    ui_agent = create_ui_deepsite_agent()
    return LlmAgent(
        name="manager_agent",
        model="gemini-2.0-flash-exp",
        description="""The manager agent is responsible for coordinating 
        the actions of the other sub-agents based on user query intent.""",
        instruction="""
            You are an AI agent that routes user queries to the most suitable **subagents** based on the request type.
            ## User Query Format
            The user query will be in the following format:
            ```json
            "request": [
                {
                    "message": "User query to the application",
                    "role": "user"
                },
                {
                    "message": "Response from the application",
                    "role": "agent"
                }
            ]  
            ```
                - Take the last json with role as 'user' as current query.
                - Take the rest of the json's irrespective of role, as chat history for multiturn chat.
            ## Delegation Strategy
                - **Query Analysis** — Extract the user's intent from the most recent `"user"` message.
                - **Subagent Selection** — Choose the relevant subagent based on expertise.
                - **Task Assignment** — Format and forward the query.
                - **Response Handling** — Refine and return the subagent’s output.
            ## Subagent Rules
                - Subagents specialize in domains.
                - Combine outputs if multiple agents apply.
                - Fall back to direct response if no match is found.
            ## User Interaction Guidelines
                - Acknowledge and clarify delegation as needed.
                - Responses should be clear, concise, and logically structured.
            ## Constraints
                - Avoid long delays and circular delegation.
                - Ensure factual accuracy and coherent output.

            """,
        sub_agents=[hotel_agent, ui_agent],
        output_key="manager_agent",
    )


root_agent = create_manager_agent()
