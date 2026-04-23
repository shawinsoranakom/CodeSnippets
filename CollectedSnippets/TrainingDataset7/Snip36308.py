def mock_quote(*args, **kwargs):
            # The second frame is the call to repercent_broken_unicode().
            decoded_paths.append(inspect.currentframe().f_back.f_locals["path"])
            return quote(*args, **kwargs)