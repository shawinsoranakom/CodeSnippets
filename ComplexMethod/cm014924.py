def check_deterministic(self, key: str, value: object):
        if isinstance(value, (int, float, bool)) or value is None:
            return
        elif isinstance(value, str):
            self.assertFalse(
                PATH_PATTERN.match(value),
                f"Detected path in config value '{value}', key='{key}', "
                "this may cause non-deterministic behavior in compile caching.",
            )
            if USERNAME:
                self.assertNotIn(
                    USERNAME,
                    value,
                    f"Detected username in config value '{value}', key='{key}', "
                    "this may cause non-deterministic behavior in compile caching.",
                )
            if HOSTNAME:
                self.assertNotIn(
                    HOSTNAME,
                    value,
                    f"Detected hostname in config value '{value}', key='{key}', "
                    "this may cause non-deterministic behavior in compile caching.",
                )
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                self.check_deterministic(f"{key}[{i}]", item)
        elif isinstance(value, dict):
            for k, v in value.items():
                self.check_deterministic(f"{key}[{k}]", v)
        else:
            self.fail(f"Unexpected type: {type(value)}")