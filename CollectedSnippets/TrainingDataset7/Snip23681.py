def test_overwrite_queryset(self):
        test_view = views.CustomMultipleObjectMixinView()
        test_view.get(self.rf.get("/"))
        queryset = [{"name": "Lennon"}, {"name": "Ono"}]
        self.assertNotEqual(test_view.queryset, queryset)
        # Overwrite the view's queryset with queryset from kwarg
        context = test_view.get_context_data(object_list=queryset)
        self.assertEqual(context["object_list"], queryset)