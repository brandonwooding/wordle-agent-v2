import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai.types import Content, Part
from tools.browser_manager import BrowserManager

class WordleExecutor(BaseAgent):
    """
    Mechanical agent that handles typing, the Enter delay, 
    and structured feedback capture.
    """

    def create_text_event(self, text: str) -> Event:
        return Event(
            author=self.name,
            content=Content(parts=[Part(text=text)])
        )

    async def _run_async_impl(self, ctx):
        driver = BrowserManager.get_driver()
        plan = ctx.session.state.get("current_plan")
        
        if not plan:
            yield self.create_text_event("❌ No 'current_plan' found in state.")
            return

        word = plan["guess"].upper()
        yield self.create_text_event(f"⌨️ Typing: {word}")

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.click() # Focus the game

            # 1. Type the 5 letters
            body.send_keys(word)
            
            # 2. MANDATORY DELAY
            # Gives the UI time to process the 5th letter animation
            await asyncio.sleep(0.5) 
            
            # 3. Press Enter
            body.send_keys(Keys.ENTER)
            yield self.create_text_event("✅ Submitted. Waiting for tiles to flip...")

                # 1. THE VALIDATION WAIT
            await asyncio.sleep(1.5) 
            
            # Wordle shows a "Toast" message if the word is invalid.
            # We check if the letters are still "shaking" or if an error message appeared.
            try:
                invalid_toast = driver.find_elements(By.XPATH, "//*[contains(text(), 'Not in word list')]")
                
                if invalid_toast:
                    yield self.create_text_event(f"❌ {word} is not a valid Wordle word. Cleaning up...")
                    
                    # A. CLEAR THE BOARD (Mechanical Fix)
                    for _ in range(5):
                        body.send_keys(Keys.BACKSPACE)
                    
                    # B. UPDATE STATE (State Fix)
                    # We don't append to history. Instead, we log the failure 
                    # in a separate key so the Strategist knows to skip it.
                    ctx.session.state["last_error"] = f"{word} is not in the dictionary."
                    return # Exit early so we don't scrape colors
            except:
                pass

            # 4. ANIMATION DELAY (Results)
            # Tiles flip one by one. 3 seconds ensures all 5 are finished.
            await asyncio.sleep(3.0) 

            # 5. STRUCTURED SCRAPING
            tiles = driver.find_elements(By.CSS_SELECTOR, 'div[data-state]:not([data-state="empty"])')
            last_five = tiles[-5:]
            
            feedback_list = []
            for index, t in enumerate(last_five):
                feedback_list.append({
                    "slot": index,
                    "letter": t.text.upper(),
                    "result": t.get_attribute("data-state") # correct/present/absent
                })

            # 6. NESTED HISTORY UPDATE
            history = ctx.session.state.get("board_history", [])
            
            turn_data = {
                "turn_number": len(history) + 1,
                "guess": word,
                "feedback": feedback_list
            }

            history.append(turn_data)
            ctx.session.state["board_history"] = history
            
            yield self.create_text_event(f"📊 Turn {turn_data['turn_number']} results captured and saved.")

        except Exception as e:
            yield self.create_text_event(f"⚠️ Selenium Error: {str(e)}")

guess_executor = WordleExecutor(name="guess_executor")