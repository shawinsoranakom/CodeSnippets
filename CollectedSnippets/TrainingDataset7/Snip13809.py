def dark(self):
        # Navigate to a page before executing a script.
        self.selenium.get(self.live_server_url)
        self.selenium.execute_script("localStorage.setItem('theme', 'dark');")
        with self.desktop_size():
            try:
                yield
            finally:
                self.selenium.execute_script("localStorage.removeItem('theme');")