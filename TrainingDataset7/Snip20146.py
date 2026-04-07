def test_bilateral_upper(self):
        with register_lookup(models.CharField, UpperBilateralTransform):
            author1 = Author.objects.create(name="Doe")
            author2 = Author.objects.create(name="doe")
            author3 = Author.objects.create(name="Foo")
            self.assertCountEqual(
                Author.objects.filter(name__upper="doe"),
                [author1, author2],
            )
            self.assertSequenceEqual(
                Author.objects.filter(name__upper__contains="f"),
                [author3],
            )