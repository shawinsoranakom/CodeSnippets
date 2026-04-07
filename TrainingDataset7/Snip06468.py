def _clear(self, queryset, bulk):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.model, instance=self.instance)
            queryset = queryset.using(db)
            if bulk:
                # `QuerySet.delete()` creates its own atomic block which
                # contains the `pre_delete` and `post_delete` signal handlers.
                queryset.delete()
            else:
                with transaction.atomic(using=db, savepoint=False):
                    for obj in queryset:
                        obj.delete()