def _rename(self, apps, schema_editor, old_model, new_model):
        ContentType = apps.get_model("contenttypes", "ContentType")
        db = schema_editor.connection.alias
        if not router.allow_migrate_model(db, ContentType):
            return

        try:
            content_type = ContentType.objects.db_manager(db).get_by_natural_key(
                self.app_label, old_model
            )
        except ContentType.DoesNotExist:
            pass
        else:
            content_type.model = new_model
            try:
                with transaction.atomic(using=db):
                    content_type.save(using=db, update_fields={"model"})
            except IntegrityError:
                # Gracefully fallback if a stale content type causes a
                # conflict. Warn the user so they can run the
                # remove_stale_contenttypes management command.
                warnings.warn(
                    f"Could not rename content type '{self.app_label}.{old_model}' "
                    f"to '{new_model}' due to an existing conflicting content type. "
                    "Run 'remove_stale_contenttypes' to clean up stale entries.",
                    RuntimeWarning,
                )
                content_type.model = old_model
            else:
                # Clear the cache as the `get_by_natural_key()` call will cache
                # the renamed ContentType instance by its old model name.
                ContentType.objects.clear_cache()