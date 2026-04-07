def test_invalid_order_by_raw_column_alias(self):
        msg = (
            "Cannot resolve keyword 'queries_author.name' into field. Choices "
            "are: cover, created, creator, creator_id, id, modified, name, "
            "note, note_id, tags"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Item.objects.values("creator__name").order_by("queries_author.name")