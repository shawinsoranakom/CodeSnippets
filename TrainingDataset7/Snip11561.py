def clear(self):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.through, instance=self.instance)
            self._clear_base(using=db)