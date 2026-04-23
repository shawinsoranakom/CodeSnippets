def test_incorrect_content_type(self):
        class BadModel(models.Model):
            content_type = models.PositiveIntegerField()

        msg = (
            "fk_name 'generic_relations.BadModel.content_type' is not a ForeignKey to "
            "ContentType"
        )
        with self.assertRaisesMessage(Exception, msg):
            generic_inlineformset_factory(BadModel, TaggedItemForm)