def get_objects():
            from django.db.migrations.loader import MigrationLoader

            loader = MigrationLoader(self.connection)
            for app_config in apps.get_app_configs():
                if (
                    app_config.models_module is not None
                    and app_config.label in loader.migrated_apps
                    and app_config.name not in settings.TEST_NON_SERIALIZED_APPS
                ):
                    for model in app_config.get_models():
                        if model._meta.can_migrate(
                            self.connection
                        ) and router.allow_migrate_model(self.connection.alias, model):
                            queryset = model._base_manager.using(
                                self.connection.alias,
                            ).order_by(model._meta.pk.name)
                            chunk_size = (
                                2000 if queryset._prefetch_related_lookups else None
                            )
                            yield from queryset.iterator(chunk_size=chunk_size)