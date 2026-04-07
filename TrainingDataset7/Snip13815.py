def disable_implicit_wait(self):
        """Disable the default implicit wait."""
        self.selenium.implicitly_wait(0)
        try:
            yield
        finally:
            self.selenium.implicitly_wait(self.implicit_wait)