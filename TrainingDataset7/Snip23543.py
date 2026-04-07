def test_unsaved_generic_foreign_key_parent_save(self):
        quartz = Mineral(name="Quartz", hardness=7)
        tagged_item = TaggedItem(tag="shiny", content_object=quartz)
        msg = (
            "save() prohibited to prevent data loss due to unsaved related object "
            "'content_object'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            tagged_item.save()