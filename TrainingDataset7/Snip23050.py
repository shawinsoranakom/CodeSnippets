def make_method_counter(func):
            """Add a counter to func for the number of times it's called."""
            counter = Counter()
            counter.call_count = 0

            def mocked_func(*args, **kwargs):
                counter.call_count += 1
                return func(*args, **kwargs)

            return mocked_func, counter