from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
import os
from pathlib import Path
from pydantic import BaseModel, Field
from tools.logging import before_agent_callback, before_model_callback, after_agent_callback, after_model_callback

dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=dotenv_path)
api = os.getenv("GOOGLE_API_KEY")

# Get the path to instructions.md relative to this agent.py file
current_dir = Path(__file__).parent
instructions_path = current_dir / "instructions.md"

with open(instructions_path, "r", encoding="utf-8") as f:
    agent_instructions = f.read()

class GameGuess(BaseModel):
    guess: str = Field(description="single 5-letter word guess")
    rationale: str = Field(description="A short explanation of why this guess was chosen")

guess_strategy_agent = Agent(
    name="wordle_strategy_agent",
    description="Strategy agent that formulates a good guess for the game Wordle",
    model="gemini-2.0-flash",
    instruction=agent_instructions,
    # tools=[end_game], 
    output_schema=GameGuess, 
    output_key = "current_plan", 
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
