def modifier_key(self):
        from selenium.webdriver.common.keys import Keys

        return Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL