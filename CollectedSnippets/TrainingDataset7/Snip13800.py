def __exit__(self, exc_type, exc_value, traceback):
        self.selenium.set_window_size(self.old_size["width"], self.old_size["height"])