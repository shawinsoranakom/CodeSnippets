def mocked_tick(*args):
            yield
            self.reloader.stop()
            return