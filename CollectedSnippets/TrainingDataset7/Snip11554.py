def _add_base(self, *objs, through_defaults=None, using=None, raw=False):
            db = using or router.db_for_write(self.through, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                self._add_items(
                    self.source_field_name,
                    self.target_field_name,
                    *objs,
                    through_defaults=through_defaults,
                    using=db,
                    raw=raw,
                )
                # If this is a symmetrical m2m relation to self, add the mirror
                # entry in the m2m table.
                if self.symmetrical:
                    self._add_items(
                        self.target_field_name,
                        self.source_field_name,
                        *objs,
                        through_defaults=through_defaults,
                        using=db,
                        raw=raw,
                    )