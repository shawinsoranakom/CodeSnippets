def small_screen_size(self):
        with ChangeWindowSize(1024, 768, self.selenium):
            yield