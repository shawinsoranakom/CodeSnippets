def test_icontains(self):
        # Using the __icontains lookup with ArrayField is inefficient.
        instance = CharArrayModel.objects.create(field=["FoO"])
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(field__icontains="foo"), [instance]
        )