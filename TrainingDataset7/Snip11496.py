def get_queryset(self, *, instance):
        return self.field.remote_field.model._base_manager.db_manager(
            hints={"instance": instance}
        ).fetch_mode(instance._state.fetch_mode)