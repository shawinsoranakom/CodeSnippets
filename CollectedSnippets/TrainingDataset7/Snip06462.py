def add(self, *objs, bulk=True):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.model, instance=self.instance)

            def check_and_update_obj(obj):
                if not isinstance(obj, self.model):
                    raise TypeError(
                        "'%s' instance expected, got %r"
                        % (self.model._meta.object_name, obj)
                    )
                setattr(obj, self.content_type_field_name, self.content_type)
                setattr(obj, self.object_id_field_name, self.pk_val)

            if bulk:
                pks = []
                for obj in objs:
                    if obj._state.adding or obj._state.db != db:
                        raise ValueError(
                            "%r instance isn't saved. Use bulk=False or save "
                            "the object first." % obj
                        )
                    check_and_update_obj(obj)
                    pks.append(obj.pk)

                self.model._base_manager.using(db).filter(pk__in=pks).update(
                    **{
                        self.content_type_field_name: self.content_type,
                        self.object_id_field_name: self.pk_val,
                    }
                )
            else:
                with transaction.atomic(using=db, savepoint=False):
                    for obj in objs:
                        check_and_update_obj(obj)
                        obj.save()