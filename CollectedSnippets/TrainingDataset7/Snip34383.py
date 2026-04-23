def set_dirs(self, dirs):
        original_dirs = self.engine.dirs
        self.engine.dirs = dirs
        try:
            yield
        finally:
            self.engine.dirs = original_dirs