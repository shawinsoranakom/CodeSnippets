def check_allowed_hosts(cls, expected):
        if settings.ALLOWED_HOSTS != expected:
            raise RuntimeError(f"{settings.ALLOWED_HOSTS} != {expected}")