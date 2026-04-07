def trigger_resize(self):
        width = self.selenium.get_window_size()["width"]
        height = self.selenium.get_window_size()["height"]
        self.selenium.set_window_size(width + 1, height)
        self.wait_page_ready()
        self.selenium.set_window_size(width, height)
        self.wait_page_ready()