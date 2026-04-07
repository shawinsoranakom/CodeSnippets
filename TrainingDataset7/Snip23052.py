def mocked_func(*args, **kwargs):
                counter.call_count += 1
                return func(*args, **kwargs)