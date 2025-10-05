from google.adk.agents import LlmAgent

chat_agent = LlmAgent(
    name="chat_agent",
    model="gemini-2.0-flash",
    description="Simple chat agent",
    instruction="""
    You are a helpful chat agent that casually chats with the user.
    """,
)