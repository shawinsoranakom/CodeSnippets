def check(cls, *args, **kwargs):
        cls.system_check_run_count += 1
        return super().check(**kwargs)