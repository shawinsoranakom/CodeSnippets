def get_capability(cls, browser):
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

        caps = getattr(DesiredCapabilities, browser.upper())
        if browser == "chrome":
            caps["goog:loggingPrefs"] = {"browser": "ALL"}

        return caps