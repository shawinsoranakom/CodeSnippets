def wait_until(self, callback, timeout=10):
        """
        Block the execution of the tests until the specified callback returns a
        value that is not falsy. This method can be called, for example, after
        clicking a link or submitting a form. See the other public methods that
        call this function for more details.
        """
        from selenium.webdriver.support.wait import WebDriverWait

        WebDriverWait(self.selenium, timeout).until(callback)