def ready(self):
        post_migrate.connect(create_default_site, sender=self)
        checks.register(check_site_id, checks.Tags.sites)