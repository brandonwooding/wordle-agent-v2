import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.adk.agents import BaseAgent
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part
from tools.browser_manager import BrowserManager
from typing import Tuple, Optional

class WordleExecutor(BaseAgent):
    """
    Mechanical agent that handles typing, the Enter delay, 
    and structured feedback capture.
    """

    def create_text_event(self, text: str, state_changes: Optional[dict] = None) -> Tuple[Event, Optional[EventActions]]:
        event = Event(author=self.name, content=Content(parts=[Part(text=text)]))
        actions = EventActions(state_delta=state_changes) if state_changes else None
        return event, actions

    async def _run_async_impl(self, ctx):
        driver = BrowserManager.get_driver()
        wait = WebDriverWait(driver, 10)
        plan = ctx.session.state.get("current_plan")
        
        if not plan:
            yield self.create_text_event("❌ No 'current_plan' found in state.")
            return

        word = plan["guess"].upper()
        yield self.create_text_event(f"⌨️ Typing: {word}")

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.click()

            body.send_keys(word)
            await asyncio.sleep(0.5) 
            body.send_keys(Keys.ENTER)
            yield self.create_text_event("✅ Submitted. Waiting for validation...")

            # CHECK FOR WIN CONDITION FIRST
            won_game = False
            try:
                win_toast = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//*[contains(text(), 'Genius') or contains(text(), 'Magnificent') or contains(text(), 'Impressive') or contains(text(), 'Splendid') or contains(text(), 'Great') or contains(text(), 'Phew')]"
                    ))
                )
                if win_toast.is_displayed():
                    won_game = True
                    yield self.create_text_event("🔍 Detected win toast message!")
            except:
                pass

            if won_game:
                await asyncio.sleep(2.0)
                
                tiles = driver.find_elements(By.CSS_SELECTOR, 'div[data-state]:not([data-state="empty"])')
                last_five = tiles[-5:]
                
                feedback_list = []
                for index, t in enumerate(last_five):
                    feedback_list.append({
                        "slot": index,
                        "letter": t.text.upper(),
                        "result": "correct"
                    })
                
                history = ctx.session.state.get("board_history", [])
                turn_data = {
                    "turn_number": len(history) + 1,
                    "guess": word,
                    "feedback": feedback_list,
                    "is_winning_guess": True
                }
                history.append(turn_data)
                
                # Update state first
                ctx.session.state["board_history"] = history
                ctx.session.state["game_status"] = "won"
                ctx.session.state["winning_word"] = word
                
                # Yield with state_delta to show in UI
                yield self.create_text_event(
                    f"🎉 SUCCESS! {word} is correct! Game won in {len(history)} guesses!",
                    state_changes={
                        "board_history": history,
                        "game_status": "won",
                        "winning_word": word
                    }
                )
                return

            # CHECK FOR INVALID WORD
            is_invalid = False
            try:
                invalid_toast = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//*[contains(text(), 'Not in word list') or contains(text(), 'not in word list')]"
                    ))
                )
                if invalid_toast.is_displayed():
                    is_invalid = True
                    yield self.create_text_event("🔍 Detected 'Not in word list' toast")
            except:
                pass
            
            if not is_invalid:
                await asyncio.sleep(1.5)
                tiles = driver.find_elements(By.CSS_SELECTOR, 'div[data-state]')
                tbd_tiles = [t for t in tiles if t.get_attribute("data-state") == "tbd"]
                
                if len(tbd_tiles) >= 5:
                    is_invalid = True
                    yield self.create_text_event("🔍 Detected tiles still in 'tbd' state - word invalid")
            
            if is_invalid:
                yield self.create_text_event(f"❌ {word} is not a valid Wordle word. Cleaning up...")
                
                for _ in range(5):
                    body.send_keys(Keys.BACKSPACE)
                
                # Update state first
                ctx.session.state["last_error"] = f"{word} is not in the dictionary."
                invalid_words = ctx.session.state.get("invalid_words", []) + [word]
                ctx.session.state["invalid_words"] = invalid_words
                
                # Yield with state_delta
                yield self.create_text_event(
                    f"🚫 Word rejected. Strategist should try again.",
                    state_changes={
                        "last_error": ctx.session.state["last_error"],
                        "invalid_words": invalid_words
                    }
                )
                return

            # NORMAL CASE
            yield self.create_text_event("✅ Word accepted. Waiting for tiles to flip...")
            await asyncio.sleep(3.0)

            tiles = driver.find_elements(By.CSS_SELECTOR, 'div[data-state]:not([data-state="empty"])')
            last_five = tiles[-5:]
            
            feedback_list = []
            all_correct = True
            
            for index, t in enumerate(last_five):
                state = t.get_attribute("data-state")
                feedback_list.append({
                    "place": index + 1,
                    "letter": t.text.upper(),
                    "result": state
                })
                if state != "correct":
                    all_correct = False

            history = ctx.session.state.get("board_history", [])
            turn_number = len(history) + 1
            
            turn_data = {
                "turn_number": turn_number,
                "guess": word,
                "feedback": feedback_list
            }

            if all_correct:
                turn_data["is_winning_guess"] = True
                history.append(turn_data)
                
                ctx.session.state["board_history"] = history
                ctx.session.state["game_status"] = "won"
                ctx.session.state["winning_word"] = word
                
                yield self.create_text_event(
                    f"🎉 SUCCESS! {word} is correct! Game won in {turn_number} guesses!",
                    state_changes={
                        "board_history": history,
                        "game_status": "won",
                        "winning_word": word
                    }
                )
                return

            if turn_number >= 6:
                turn_data["is_final_guess"] = True
                history.append(turn_data)
                
                ctx.session.state["board_history"] = history
                ctx.session.state["game_status"] = "lost"
                
                yield self.create_text_event(
                    f"😞 Game over. Failed to guess the word in 6 tries.",
                    state_changes={
                        "board_history": history,
                        "game_status": "lost"
                    }
                )
                return

            history.append(turn_data)
            ctx.session.state["board_history"] = history
            
            yield self.create_text_event(
                f"📊 Turn {turn_number} results saved. Continue playing...",
                state_changes={"board_history": history}
            )

        except Exception as e:
            yield self.create_text_event(f"⚠️ Selenium Error: {str(e)}")
            ctx.session.state["last_error"] = str(e)

guess_executor = WordleExecutor(name="guess_executor")