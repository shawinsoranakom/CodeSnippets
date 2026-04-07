def test_object_in_get_context_data(self):
        # Checks 'object' key presence in dict returned by get_context_date
        # #20234
        test_view = views.CustomSingleObjectView()
        context = test_view.get_context_data()
        self.assertEqual(context["object"], test_view.object)