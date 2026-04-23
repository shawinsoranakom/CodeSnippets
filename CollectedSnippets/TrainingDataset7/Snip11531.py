def get_queryset(self):
            # Even if this relation is not to pk, we require still pk value.
            # The wish is that the instance has been already saved to DB,
            # although having a pk value isn't a guarantee of that.
            if not self.instance._is_pk_set():
                raise ValueError(
                    f"{self.instance.__class__.__name__!r} instance needs to have a "
                    f"primary key value before this relationship can be used."
                )
            try:
                return self.instance._prefetched_objects_cache[
                    self.field.remote_field.cache_name
                ]
            except (AttributeError, KeyError):
                queryset = super().get_queryset()
                return self._apply_rel_filters(queryset)