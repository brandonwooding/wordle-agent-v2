import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.adk.agents import BaseAgent
from tools.browser_manager import BrowserManager
from google.adk.events import Event
from google.genai.types import Content, Part


class WordleOpener(BaseAgent):

    def create_text_event(self, text: str) -> Event:
        return Event(
            author=self.name,
            content=Content(parts=[Part(text=text)])
        )

    async def _run_async_impl(self, ctx):
        driver = BrowserManager.get_driver()
        wait = WebDriverWait(driver, 10)

        try:
            # 1. Initialize State and Navigate
            ctx.session.state["board_history"] = []
            driver.get("https://www.nytimes.com/games/wordle/index.html")
            yield self.create_text_event("🌐 Navigated to Wordle.")

            # 2. HANDLE UK PRIVACY MODAL (Fides)
            await asyncio.sleep(2)
            
            selectors = [
                (By.CSS_SELECTOR, "#fides-banner button.fides-accept-all-button"),
                (By.CSS_SELECTOR, "button[data-testid='Accept all-btn']"),
                (By.CSS_SELECTOR, "button.fides-accept-all-button"),
            ]
            
            clicked = False
            for by, selector in selectors:
                try:
                    yield self.create_text_event(f"🔍 Trying selector: {selector}")
                    fides_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", fides_btn)
                    await asyncio.sleep(0.5)
                    
                    try:
                        fides_btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", fides_btn)
                    
                    yield self.create_text_event("🍪 Privacy Preferences accepted.")
                    clicked = True
                    break
                except Exception as e:
                    yield self.create_text_event(f"⚠️ Failed: {str(e)[:100]}")
                    continue
            
            if not clicked:
                yield self.create_text_event("ℹ️ Privacy modal not detected or already cleared.")

            # Wait for modal to fully disappear
            await asyncio.sleep(3)

            # 3. THE "PLAY" BUTTON HUNT
            play_selectors = [
                (By.CSS_SELECTOR, 'button[data-testid="Play"]'),
                (By.CSS_SELECTOR, 'button[data-testid="play-button"]'),
                (By.XPATH, "//button[text()='Play']"),
                (By.XPATH, "//button[contains(@class, 'Play')]")
            ]
            
            clicked_play = False
            for by, selector in play_selectors:
                try:
                    btn = wait.until(EC.element_to_be_clickable((by, selector)))  # Use your original wait
                    btn.click()
                    yield self.create_text_event(f"🎮 Clicked 'Play' using {selector}.")
                    clicked_play = True
                    break
                except:
                    continue
            
            if not clicked_play:
                yield self.create_text_event("⚠️ Could not find Play button. Attempting to proceed regardless.")

            # Wait for game to start
            await asyncio.sleep(3)

            # 4. FORCE CLEAR MODALS
            yield self.create_text_event("🛡️ Small Change - Clearing tutorial and lingering modals...")
            
            close_selectors = [
                (By.CSS_SELECTOR, 'button[aria-label="Close"]'),
                (By.CSS_SELECTOR, 'button.close'),
                (By.CSS_SELECTOR, 'button[data-testid="close"]'),
                (By.XPATH, "//button[contains(@aria-label, 'Close')]"),
                (By.XPATH, "//button[contains(@class, 'close')]"),
                (By.CSS_SELECTOR, 'svg[data-testid="icon-close"]'),
                (By.XPATH, "//*[name()='svg' and contains(@class, 'close')]"),
            ]
            
            for by, selector in close_selectors:
                try:
                    yield self.create_text_event(f"  🔎 Trying close selector: {selector}")
                    close_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    close_btn.click()
                    yield self.create_text_event(f"  ✅ Successfully clicked: {selector}")
                    await asyncio.sleep(0.5)
                    break
                except Exception as e:
                    yield self.create_text_event(f"  ❌ Failed: {str(e)[:50]}")
                    continue
            
            """# Method 2: ESC key spam (your original)
            yield self.create_text_event("🔍 Method 2: Trying ESC key spam...")
            try:
                await asyncio.sleep(0.5)
                body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                for i in range(3):
                    body.send_keys(Keys.ESCAPE)
                    yield self.create_text_event(f"  ⌨️ Sent ESC key #{i+1}")
                    await asyncio.sleep(0.3)
                yield self.create_text_event("  ✅ ESC key spam complete")
            except Exception as e:
                yield self.create_text_event(f"  ❌ ESC failed: {str(e)[:50]}")
            
            # Method 3: Click on overlay/backdrop if it exists
            yield self.create_text_event("🔍 Method 3: Looking for overlay to click...")
            try:
                overlay = driver.find_element(By.CSS_SELECTOR, '.modal-overlay, .overlay, [class*="overlay"]')
                driver.execute_script("arguments[0].click();", overlay)
                yield self.create_text_event("  ✅ Clicked overlay")
                await asyncio.sleep(0.5)
            except Exception as e:
                yield self.create_text_event(f"  ❌ Overlay click failed: {str(e)[:50]}")"""
            
            await asyncio.sleep(1)
            yield self.create_text_event("✅ Modal clearing attempts complete.")
            
            yield self.create_text_event("✅ Board is ready.")

        except Exception as e:
            driver.save_screenshot("opener_error.png")
            yield self.create_text_event(f"❌ Opener Error: {str(e)}")

manual_wordle_opener_agent = WordleOpener(name="manual_wordle_opener")