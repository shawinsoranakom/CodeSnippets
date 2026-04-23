def _get_next_or_previous_by_FIELD(self, field, is_next, **kwargs):
        if not self._is_pk_set():
            raise ValueError("get_next/get_previous cannot be used on unsaved objects.")
        op = "gt" if is_next else "lt"
        order = "" if is_next else "-"
        param = getattr(self, field.attname)
        q = Q.create([(field.name, param), (f"pk__{op}", self.pk)], connector=Q.AND)
        q = Q.create([q, (f"{field.name}__{op}", param)], connector=Q.OR)
        qs = (
            self.__class__._default_manager.using(self._state.db)
            .filter(**kwargs)
            .filter(q)
            .order_by("%s%s" % (order, field.name), "%spk" % order)
        )
        try:
            return qs[0]
        except IndexError:
            raise self.DoesNotExist(
                "%s matching query does not exist." % self.__class__._meta.object_name
            )