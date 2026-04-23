def __enter__(self):
        self.old_size = self.selenium.get_window_size()
        self.selenium.set_window_size(*self.new_size)
        return self