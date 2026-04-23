def test_virtual_field(self):
        class RelationModel(models.Model):
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey("content_type", "object_id")

        class RelatedModelAbstract(models.Model):
            field = GenericRelation(RelationModel)

            class Meta:
                abstract = True

        class ModelAbstract(models.Model):
            field = models.CharField(max_length=100)

            class Meta:
                abstract = True

        class OverrideRelatedModelAbstract(RelatedModelAbstract):
            field = models.CharField(max_length=100)

        class ExtendModelAbstract(ModelAbstract):
            field = GenericRelation(RelationModel)

        self.assertIsInstance(
            OverrideRelatedModelAbstract._meta.get_field("field"), models.CharField
        )
        self.assertIsInstance(
            ExtendModelAbstract._meta.get_field("field"), GenericRelation
        )