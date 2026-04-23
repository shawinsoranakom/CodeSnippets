def now(self):
                self.elapsed_seconds += 1
                return datetime.datetime(
                    2006,
                    10,
                    25,
                    14,
                    30,
                    45 + self.elapsed_seconds,
                    microseconds,
                )