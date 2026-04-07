def test_generic_relation_related_name_default(self):
        # GenericRelation isn't usable from the reverse side by default.
        msg = (
            "Cannot resolve keyword 'vegetable' into field. Choices are: "
            "animal, content_object, content_type, content_type_id, id, "
            "manualpk, object_id, tag, valuabletaggeditem"
        )
        with self.assertRaisesMessage(FieldError, msg):
            TaggedItem.objects.filter(vegetable__isnull=True)