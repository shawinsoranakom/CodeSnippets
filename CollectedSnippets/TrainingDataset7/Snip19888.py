def test_valid_self_referential_generic_relationship(self):
        class Model(models.Model):
            rel = GenericRelation("Model")
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey("content_type", "object_id")

        self.assertEqual(Model.rel.field.check(), [])