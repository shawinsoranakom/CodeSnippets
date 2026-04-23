def ready(self):
        checks.register(check_finders, checks.Tags.staticfiles)
        checks.register(check_storages, checks.Tags.staticfiles)