def create_webdriver(self):
        options = self.create_options()
        if self.selenium_hub:
            from selenium import webdriver

            for key, value in self.get_capability(self.browser).items():
                options.set_capability(key, value)

            return webdriver.Remote(command_executor=self.selenium_hub, options=options)
        return self.import_webdriver(self.browser)(options=options)