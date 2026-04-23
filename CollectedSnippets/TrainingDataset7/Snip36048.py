def tick_twice(self):
        ticker = self.reloader.tick()
        next(ticker)
        yield
        next(ticker)