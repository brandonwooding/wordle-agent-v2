from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.load_artifacts_tool import load_artifacts_tool
from google.genai import types
from dotenv import load_dotenv
import os
import time
import warnings
from pathlib import Path
from PIL import Image

import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

warnings.filterwarnings("ignore", category=UserWarning)

dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=dotenv_path)
api = os.getenv("GOOGLE_API_KEY")

# Get the path to instructions.md relative to this agent.py file
current_dir = Path(__file__).parent
instructions_path = current_dir / "instructions.md"

with open(instructions_path, "r", encoding="utf-8") as f:
    agent_instructions = f.read()

# In your web_pager_opener_agent.py
from tools.browser_manager import BrowserManager

# Replace your 'if not DISABLE_WEB_DRIVER' block with this:
driver = BrowserManager.get_driver()

def go_to_url(url: str) -> str:
    """Navigates the browser to the given URL."""
    print(f"🌐 Navigating to URL: {url}")  # Added print statement
    driver.get(url.strip())
    return f"Navigated to URL: {url}"


def take_screenshot(tool_context: ToolContext) -> dict:
    """Takes a screenshot and saves it with the given filename. called 'load artifacts' after to load the image"""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    print(f"📸 Taking screenshot and saving as: {filename}")
    driver.save_screenshot(filename)

    image = Image.open(filename)

    tool_context.save_artifact(
        filename,
        types.Part.from_bytes(data=image.tobytes(), mime_type="image/png"),
    )

    return {"status": "ok", "filename": filename}


def click_at_coordinates(x: int, y: int) -> str:
    """Clicks at the specified coordinates on the screen."""
    driver.execute_script(f"window.scrollTo({x}, {y});")
    driver.find_element(By.TAG_NAME, "body").click()


def find_element_with_text(text: str) -> str:
    """Finds an element on the page with the given text."""
    print(f"🔍 Finding element with text: '{text}'")  # Added print statement

    try:
        element = driver.find_element(By.XPATH, f"//*[text()='{text}']")
        if element:
            return "Element found."
        else:
            return "Element not found."
    except selenium.common.exceptions.NoSuchElementException:
        return "Element not found."
    except selenium.common.exceptions.ElementNotInteractableException:
        return "Element not interactable, cannot click."


def get_element_text(by: str, value: str, timeout: int) -> str:
    """Gets the text of a specific element located by the given method and value."""
    print(f"🧾 Getting text of element by {by}='{value}' (timeout={timeout}s)")

    by_mapping = {
        "css": By.CSS_SELECTOR,
        "xpath": By.XPATH,
        "id": By.ID,
        "name": By.NAME,
        "tag": By.TAG_NAME,
        "class": By.CLASS_NAME,
        "link_text": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT
    }

    try:
        if by not in by_mapping:
            return f"❌ Unsupported locator method: '{by}'"

        locator = (by_mapping[by], value)
        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        text = element.text.strip()
        return f"✅ Element text: {text}" if text else "⚠️ Element found, but text is empty."

    except Exception as e:
        return f"❌ Error getting element text: {e}"


def extract_visible_text() -> str:
    """Extracts all visible text from the current page."""
    print("📄 Extracting visible text from the page...")

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        return body.text.strip()
    except selenium.common.exceptions.NoSuchElementException:
        return "No <body> element found on the page."
    except Exception as e:
        return f"Error extracting text: {e}"


def click_element_with_text(text: str) -> str:
    """Clicks on an element on the page with the given text."""
    print(f"🖱️ Clicking element with text: '{text}'")  # Added print statement

    try:
        element = driver.find_element(By.XPATH, f"//*[text()='{text}']")
        element.click()
        return f"Clicked element with text: {text}"
    except selenium.common.exceptions.NoSuchElementException:
        return "Element not found, cannot click."
    except selenium.common.exceptions.ElementNotInteractableException:
        return "Element not interactable, cannot click."
    except selenium.common.exceptions.ElementClickInterceptedException:
        return "Element click intercepted, cannot click."


def click_element(by: str, value: str, timeout: int) -> str:
    """Clicks an element located by a specific selector type and value."""
    print(f"🖱️ Clicking element by {by}='{value}' (timeout={timeout}s)")

    by_mapping = {
        "css": By.CSS_SELECTOR,
        "xpath": By.XPATH,
        "id": By.ID,
        "name": By.NAME,
        "tag": By.TAG_NAME,
        "class": By.CLASS_NAME
    }

    if by not in by_mapping:
        return f"❌ Unsupported locator method: '{by}'"

    try:
        locator = (by_mapping[by], value)
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        return "✅ Element clicked."
    except Exception as e:
        return f"❌ Error clicking element: {e}"



def enter_text_into_element(text_to_enter: str, element_id: str) -> str:
    """Enters text into an element with the given ID."""
    print(
        f"📝 Entering text '{text_to_enter}' into element with ID: {element_id}"
    )  # Added print statement

    try:
        input_element = driver.find_element(By.ID, element_id)
        input_element.send_keys(text_to_enter)
        return (
            f"Entered text '{text_to_enter}' into element with ID: {element_id}"
        )
    except selenium.common.exceptions.NoSuchElementException:
        return "Element with given ID not found."
    except selenium.common.exceptions.ElementNotInteractableException:
        return "Element not interactable, cannot click."


def scroll_down_screen() -> str:
    """Scrolls down the screen by a moderate amount."""
    print("⬇️ scroll the screen")  # Added print statement
    driver.execute_script("window.scrollBy(0, 500)")
    return "Scrolled down the screen."


def get_page_source() -> str:
    LIMIT = 1000000
    """Returns the current page source."""
    print("📄 Getting page source...")  # Added print statement
    return driver.page_source[0:LIMIT]


web_pager_opener_agent = Agent(
    model="gemini-2.5-flash",
    name="browser_agent",
    description="opens, naviagates and interacts with web pages",
    instruction=agent_instructions.format(website="https://www.nytimes.com/games/wordle/index.html", custom_instructions="Click the 'Play' button"),
    tools=[
        go_to_url,
        take_screenshot,
        find_element_with_text,
        get_element_text,
        extract_visible_text,
        click_element_with_text,
        click_element,
        enter_text_into_element,
        scroll_down_screen,
        get_page_source,
        load_artifacts_tool,
    ],
)