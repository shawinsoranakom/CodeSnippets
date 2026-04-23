def test_charlink_filter(self):
        oddrel = OddRelation1.objects.create(name="clink")
        CharLink.objects.create(content_object=oddrel, value="value")
        self.assertSequenceEqual(
            OddRelation1.objects.filter(clinks__value="value"), [oddrel]
        )