def test_page_getitem(self):
        """
        Tests proper behavior of a paginator page __getitem__ (queryset
        evaluation, slicing, exception raised).
        """
        paginator = Paginator(Article.objects.order_by("id"), 5)
        p = paginator.page(1)

        # object_list queryset is not evaluated by an invalid __getitem__ call.
        # (this happens from the template engine when using e.g.:
        # {% page_obj.has_previous %}).
        self.assertIsNone(p.object_list._result_cache)
        msg = "Page indices must be integers or slices, not str."
        with self.assertRaisesMessage(TypeError, msg):
            p["has_previous"]
        self.assertIsNone(p.object_list._result_cache)
        self.assertNotIsInstance(p.object_list, list)

        # Make sure slicing the Page object with numbers and slice objects
        # work.
        self.assertEqual(p[0], self.articles[0])
        self.assertSequenceEqual(p[slice(2)], self.articles[:2])
        # After __getitem__ is called, object_list is a list
        self.assertIsInstance(p.object_list, list)