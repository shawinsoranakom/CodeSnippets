def test_values_queryset(self):
        msg = "Prefetch querysets cannot use raw(), values(), and values_list()."
        with self.assertRaisesMessage(ValueError, msg):
            GenericPrefetch("question", [Author.objects.values("pk")])
        with self.assertRaisesMessage(ValueError, msg):
            GenericPrefetch("question", [Author.objects.values_list("pk")])