def test_gfk_to_model_with_empty_pk(self):
        """Test related to #13085"""
        # Saving model with GenericForeignKey to model instance with an
        # empty CharField PK
        b1 = Board.objects.create(name="")
        tag = Tag(label="VP", content_object=b1)
        tag.save()