def remove(self, *objs):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.through, instance=self.instance)
            self._remove_base(*objs, using=db)