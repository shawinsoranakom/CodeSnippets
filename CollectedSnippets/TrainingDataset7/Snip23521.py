def test_add_rejects_unsaved_objects(self):
        t1 = TaggedItem(content_object=self.quartz, tag="shiny")
        msg = (
            "<TaggedItem: shiny> instance isn't saved. Use bulk=False or save the "
            "object first."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.bacon.tags.add(t1)