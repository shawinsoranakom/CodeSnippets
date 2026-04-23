def get_or_create(self, **kwargs):
            kwargs[self.content_type_field_name] = self.content_type
            kwargs[self.object_id_field_name] = self.pk_val
            db = router.db_for_write(self.model, instance=self.instance)
            return super().using(db).get_or_create(**kwargs)