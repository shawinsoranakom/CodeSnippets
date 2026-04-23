def test_use_queryset_from_view(self):
        test_view = views.CustomMultipleObjectMixinView()
        test_view.get(self.rf.get("/"))
        # Don't pass queryset as argument
        context = test_view.get_context_data()
        self.assertEqual(context["object_list"], test_view.queryset)