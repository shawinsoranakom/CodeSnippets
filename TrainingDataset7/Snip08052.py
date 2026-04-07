def handle(self, **options):
        engine = import_module(settings.SESSION_ENGINE)
        try:
            engine.SessionStore.clear_expired()
        except NotImplementedError:
            raise CommandError(
                "Session engine '%s' doesn't support clearing expired "
                "sessions." % settings.SESSION_ENGINE
            )