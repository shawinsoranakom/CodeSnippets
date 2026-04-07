def test_textlink_filter(self):
        oddrel = OddRelation2.objects.create(name="clink")
        TextLink.objects.create(content_object=oddrel, value="value")
        self.assertSequenceEqual(
            OddRelation2.objects.filter(tlinks__value="value"), [oddrel]
        )