def set_base(self, objs, *, clear=False, through_defaults=None, raw=False):
            # Force evaluation of `objs` in case it's a queryset whose value
            # could be affected by `manager.clear()`. Refs #19816.
            objs = tuple(objs)

            db = router.db_for_write(self.through, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                self._remove_prefetched_objects()
                if clear:
                    self._clear_base(using=db, raw=raw)
                    self._add_base(
                        *objs, through_defaults=through_defaults, using=db, raw=raw
                    )
                else:
                    old_ids = set(
                        self.using(db).values_list(
                            self.target_field.target_field.attname, flat=True
                        )
                    )

                    new_objs = []
                    for obj in objs:
                        fk_val = (
                            self.target_field.get_foreign_related_value(obj)[0]
                            if isinstance(obj, self.model)
                            else self.target_field.get_prep_value(obj)
                        )
                        if fk_val in old_ids:
                            old_ids.remove(fk_val)
                        else:
                            new_objs.append(obj)

                    self._remove_base(*old_ids, using=db, raw=raw)
                    self._add_base(
                        *new_objs, through_defaults=through_defaults, using=db, raw=raw
                    )