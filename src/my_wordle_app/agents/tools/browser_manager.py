import tempfile
import shutil
import os
import selenium
from selenium.webdriver.chrome.options import Options

class BrowserManager:
    _driver = None
    _temp_dir = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            # Create a unique temporary directory
            cls._temp_dir = tempfile.mkdtemp()
            
            options = Options()
            options.add_argument("--window-size=1920x1080")
            # Point Selenium to this brand-new, empty folder
            options.add_argument(f"user-data-dir={cls._temp_dir}")
            
            cls._driver = selenium.webdriver.Chrome(options=options)
        return cls._driver

    @classmethod
    def quit_driver(cls):
        """Call this to wipe the data when the game is over."""
        if cls._driver:
            cls._driver.quit()
            # Delete the temp folder to save disk space
            if cls._temp_dir and os.path.exists(cls._temp_dir):
                shutil.rmtree(cls._temp_dir)
            cls._driver = None