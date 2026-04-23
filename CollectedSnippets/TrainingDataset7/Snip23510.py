def test_query_content_object(self):
        qs = TaggedItem.objects.filter(animal__isnull=False).order_by(
            "animal__common_name", "tag"
        )
        self.assertSequenceEqual(qs, [self.hairy, self.yellow])

        mpk = ManualPK.objects.create(id=1)
        mpk.tags.create(tag="mpk")
        qs = TaggedItem.objects.filter(
            Q(animal__isnull=False) | Q(manualpk__id=1)
        ).order_by("tag")
        self.assertQuerySetEqual(qs, ["hairy", "mpk", "yellow"], lambda x: x.tag)