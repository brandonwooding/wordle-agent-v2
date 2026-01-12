from google.adk.agents import Agent
from dotenv import load_dotenv
import os
from pathlib import Path

dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=dotenv_path)
api = os.getenv("GOOGLE_API_KEY")


root_agent = Agent(
    name="poetic_agent",
    description="conversation agent that interacts in poetic language",
    model="gemini-2.0-flash",
    instruction="you are a conversational agent, that chats with humans. Use poetic language or poems to respond to the user. Keep the peoms concise, but profound.", 
)
