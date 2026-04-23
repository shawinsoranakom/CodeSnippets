def __getitem__(self, key):
        if key == "silent_fail_key":
            raise SomeException
        elif key == "noisy_fail_key":
            raise SomeOtherException
        raise KeyError