def close(self):
        self.get_stdin().read()
        super().close()