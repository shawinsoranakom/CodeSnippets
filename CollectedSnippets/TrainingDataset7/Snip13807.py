def mobile_size(self):
        with ChangeWindowSize(360, 800, self.selenium):
            yield