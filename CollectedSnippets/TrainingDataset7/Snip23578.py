def test_charlink_delete(self):
        oddrel = OddRelation1.objects.create(name="clink")
        CharLink.objects.create(content_object=oddrel)
        oddrel.delete()