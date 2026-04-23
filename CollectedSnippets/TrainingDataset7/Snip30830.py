def test_21001(self):
        foo = NamedCategory.objects.create(name="foo")
        self.assertQuerySetEqual(
            NamedCategory.objects.exclude(name=""), [foo.pk], attrgetter("pk")
        )