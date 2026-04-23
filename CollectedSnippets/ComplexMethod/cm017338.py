def _do_update(
        self,
        base_qs,
        using,
        pk_val,
        values,
        update_fields,
        forced_update,
        returning_fields,
    ):
        """
        Try to update the model. Return a list of updated fields if the model
        was updated (if an update query was done and a matching row was
        found in the DB).
        """
        filtered = base_qs.filter(pk=pk_val)
        if not values:
            # We can end up here when saving a model in inheritance chain where
            # update_fields doesn't target any field in current model. In that
            # case we just say the update succeeded. Another case ending up
            # here is a model with just PK - in that case check that the PK
            # still exists.
            if update_fields is not None or filtered.exists():
                return [()]
            return []
        if self._meta.select_on_save and not forced_update:
            # It may happen that the object is deleted from the DB right after
            # this check, causing the subsequent UPDATE to return zero matching
            # rows. The same result can occur in some rare cases when the
            # database returns zero despite the UPDATE being executed
            # successfully (a row is matched and updated). In order to
            # distinguish these two cases, the object's existence in the
            # database is again checked for if the UPDATE query returns 0.
            if not filtered.exists():
                return []
            if results := filtered._update(values, returning_fields):
                return results
            return [()] if filtered.exists() else []
        return filtered._update(values, returning_fields)