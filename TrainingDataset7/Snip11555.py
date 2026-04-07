def add(self, *objs, through_defaults=None):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.through, instance=self.instance)
            self._add_base(*objs, through_defaults=through_defaults, using=db)