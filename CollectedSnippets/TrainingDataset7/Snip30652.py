def test_ticket11811(self):
        unsaved_category = NamedCategory(name="Other")
        msg = (
            "Unsaved model instance <NamedCategory: Other> cannot be used in an ORM "
            "query."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Tag.objects.filter(pk=self.t1.pk).update(category=unsaved_category)