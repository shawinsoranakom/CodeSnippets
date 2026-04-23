def test_set(self):
        # Collector doesn't call callables used by models.SET and
        # models.SET_DEFAULT if not necessary.
        Toy.objects.create(name="test")
        Toy.objects.all().delete()
        self.assertSequenceEqual(Toy.objects.all(), [])