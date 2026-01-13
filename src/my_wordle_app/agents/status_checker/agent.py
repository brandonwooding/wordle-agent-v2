from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai.types import Content, Part
from google.adk.tools.tool_context import ToolContext


# Simple checker agent
class GameStatusChecker(BaseAgent):
    """Checks if game is over and exits loop if so."""
    
    def create_text_event(self, text: str) -> Event:
        return Event(
            author=self.name,
            content=Content(parts=[Part(text=text)])
        )
    
    async def _run_async_impl(self, ctx):
        game_status = ctx.session.state.get("game_status", "In progress")
        
        if game_status == "won":
            yield self.create_text_event("🎉 Game won! Exiting loop.")
            # Manually trigger escalate
            ctx.actions.escalate = True
            return
        
        if game_status == "lost":
            yield self.create_text_event("😞 Game lost! Exiting loop.")
            # Manually trigger escalate
            ctx.actions.escalate = True
            return
        
        # Game continues
        yield self.create_text_event("✅ Game in progress, continuing...")

game_status_checker = GameStatusChecker(name="game_status_checker")