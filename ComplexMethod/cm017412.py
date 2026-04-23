def _check_table_uniqueness(self, **kwargs):
        if (
            isinstance(self.remote_field.through, str)
            or not self.remote_field.through._meta.managed
        ):
            return []
        registered_tables = {
            model._meta.db_table: model
            for model in self.opts.apps.get_models(include_auto_created=True)
            if model != self.remote_field.through and model._meta.managed
        }
        m2m_db_table = self.m2m_db_table()
        model = registered_tables.get(m2m_db_table)
        # The second condition allows multiple m2m relations on a model if
        # some point to a through model that proxies another through model.
        if (
            model
            and model._meta.concrete_model
            != self.remote_field.through._meta.concrete_model
        ):
            if model._meta.auto_created:

                def _get_field_name(model):
                    for field in model._meta.auto_created._meta.many_to_many:
                        if field.remote_field.through is model:
                            return field.name

                opts = model._meta.auto_created._meta
                clashing_obj = "%s.%s" % (opts.label, _get_field_name(model))
            else:
                clashing_obj = model._meta.label
            if settings.DATABASE_ROUTERS:
                error_class, error_id = checks.Warning, "fields.W344"
                error_hint = (
                    "You have configured settings.DATABASE_ROUTERS. Verify "
                    "that the table of %r is correctly routed to a separate "
                    "database." % clashing_obj
                )
            else:
                error_class, error_id = checks.Error, "fields.E340"
                error_hint = None
            return [
                error_class(
                    "The field's intermediary table '%s' clashes with the "
                    "table name of '%s'." % (m2m_db_table, clashing_obj),
                    obj=self,
                    hint=error_hint,
                    id=error_id,
                )
            ]
        return []