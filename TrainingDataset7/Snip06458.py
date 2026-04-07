def _apply_rel_filters(self, queryset):
            """
            Filter the queryset for the instance this manager is bound to.
            """
            db = self._db or router.db_for_read(self.model, instance=self.instance)
            with queryset._avoid_cloning():
                return (
                    queryset.using(db)
                    .fetch_mode(self.instance._state.fetch_mode)
                    .filter(**self.core_filters)
                )