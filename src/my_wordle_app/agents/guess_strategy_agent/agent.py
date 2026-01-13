from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
import os
from pathlib import Path
from pydantic import BaseModel, Field

dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=dotenv_path)
api = os.getenv("GOOGLE_API_KEY")

# Get the path to instructions.md relative to this agent.py file
current_dir = Path(__file__).parent
instructions_path = current_dir / "instructions.md"

with open(instructions_path, "r", encoding="utf-8") as f:
    agent_instructions = f.read()

# --- Tool Definition for Exiting Loop ---
def end_game(tool_context: ToolContext):
    """Call this function when the game is won, lost, or should be terminated."""
    print(f"  [Tool Call] end_game triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {}


class GameGuess(BaseModel):
    guess: str = Field(description="single 5-letter word guess")
    rationale: str = Field(description="A short explanation of why this guess was chosen")

guess_strategy_agent = Agent(
    name="wordle_strategy_agent",
    description="Strategy agent that formulates a good guess for the game Wordle",
    model="gemini-2.0-flash",
    instruction=agent_instructions,
    tools=[end_game], 
    output_schema=GameGuess, 
    output_key = "current_plan"
)
