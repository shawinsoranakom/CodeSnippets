def test_order_with_respect_to_private_field(self):
        class PrivateFieldModel(models.Model):
            content_type = models.ForeignKey("contenttypes.ContentType", models.CASCADE)
            object_id = models.PositiveIntegerField()
            private = GenericForeignKey()

            class Meta:
                order_with_respect_to = "private"

        state = ModelState.from_model(PrivateFieldModel)
        self.assertNotIn("order_with_respect_to", state.options)