def test_textlink_delete(self):
        oddrel = OddRelation2.objects.create(name="tlink")
        TextLink.objects.create(content_object=oddrel)
        oddrel.delete()