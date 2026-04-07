def _remove_base(self, *objs, using=None, raw=False):
            db = using or router.db_for_write(self.through, instance=self.instance)
            self._remove_items(
                self.source_field_name, self.target_field_name, *objs, using=db, raw=raw
            )