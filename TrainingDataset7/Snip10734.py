def related_objects(self, related_model, related_fields, objs):
        """
        Get a QuerySet of the related model to objs via related fields.
        """
        predicate = query_utils.Q.create(
            [(f"{related_field.name}__in", objs) for related_field in related_fields],
            connector=query_utils.Q.OR,
        )
        return related_model._base_manager.using(self.using).filter(predicate)