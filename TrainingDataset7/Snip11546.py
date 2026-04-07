def _apply_rel_filters(self, queryset):
            """
            Filter the queryset for the instance this manager is bound to.
            """
            with queryset._avoid_cloning():
                queryset._add_hints(instance=self.instance)
                if self._db:
                    queryset = queryset.using(self._db)
                queryset._fetch_mode = self.instance._state.fetch_mode
                queryset._defer_next_filter = True
                return queryset._next_is_sticky().filter(**self.core_filters)