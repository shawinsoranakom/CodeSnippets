def test_create_view_with_restricted_fields(self):
        class MyCreateView(CreateView):
            model = Author
            fields = ["name"]

        self.assertEqual(list(MyCreateView().get_form_class().base_fields), ["name"])