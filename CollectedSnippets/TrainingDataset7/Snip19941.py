def test_raw_queryset(self):
        msg = "Prefetch querysets cannot use raw(), values(), and values_list()."
        with self.assertRaisesMessage(ValueError, msg):
            GenericPrefetch("question", [Author.objects.raw("select pk from author")])