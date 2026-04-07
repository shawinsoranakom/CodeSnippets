def test_values_queryset(self):
        msg = "Prefetch querysets cannot use raw(), values(), and values_list()."
        with self.assertRaisesMessage(ValueError, msg):
            Prefetch("houses", House.objects.values("pk"))
        with self.assertRaisesMessage(ValueError, msg):
            Prefetch("houses", House.objects.values_list("pk"))
        # That error doesn't affect managers with custom ModelIterable
        # subclasses
        self.assertIs(
            Teacher.objects_custom.all()._iterable_class, ModelIterableSubclass
        )
        Prefetch("teachers", Teacher.objects_custom.all())