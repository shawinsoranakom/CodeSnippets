def run_django_admin(self, args, settings_file=None, umask=-1):
        return self.run_test(["-m", "django", *args], settings_file, umask=umask)