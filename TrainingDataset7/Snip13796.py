def create_options(self):
        options = self.import_options(self.browser)()
        if self.browser == "chrome":
            # Disable Google Password Manager "Data Breach" alert pop-ups.
            options.add_argument("--guest")
            options.add_argument("--disable-infobars")
        if self.headless:
            match self.browser:
                case "chrome" | "edge":
                    options.add_argument("--headless=new")
                case "firefox":
                    options.add_argument("-headless")
        return options