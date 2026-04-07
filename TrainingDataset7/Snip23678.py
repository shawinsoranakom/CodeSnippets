def test_object_at_custom_name_in_context_data(self):
        # Checks 'pony' key presence in dict returned by get_context_date
        test_view = views.CustomSingleObjectView()
        test_view.context_object_name = "pony"
        context = test_view.get_context_data()
        self.assertEqual(context["pony"], test_view.object)