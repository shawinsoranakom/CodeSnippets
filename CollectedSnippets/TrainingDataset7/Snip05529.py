def ready(self):
        super().ready()
        self.module.autodiscover()