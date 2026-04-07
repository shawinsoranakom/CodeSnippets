def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        """
        Return all objects related to ``objs`` via this ``GenericRelation``.
        """
        return self.remote_field.model._base_manager.db_manager(using).filter(
            **{
                "%s__pk"
                % self.content_type_field_name: ContentType.objects.db_manager(using)
                .get_for_model(self.model, for_concrete_model=self.for_concrete_model)
                .pk,
                "%s__in" % self.object_id_field_name: [obj.pk for obj in objs],
            }
        )