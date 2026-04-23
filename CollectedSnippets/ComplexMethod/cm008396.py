def _RETURN_TYPE(cls):
        """What the extractor returns: "video", "playlist", "any", or None (Unknown)"""
        tests = tuple(cls.get_testcases(include_onlymatching=False))
        if not tests:
            return None
        elif not any(k.startswith('playlist') for test in tests for k in test):
            return 'video'
        elif all(any(k.startswith('playlist') for k in test) for test in tests):
            return 'playlist'
        return 'any'