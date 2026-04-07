def __init__(self):
                # Freeze time, calling `sleep` will manually advance it.
                self._time = time.time()