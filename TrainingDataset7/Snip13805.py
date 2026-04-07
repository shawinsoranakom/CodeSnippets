def desktop_size(self):
        with ChangeWindowSize(1280, 720, self.selenium):
            yield