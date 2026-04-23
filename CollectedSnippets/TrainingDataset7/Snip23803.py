def test_create_view_all_fields(self):
        class MyCreateView(CreateView):
            model = Author
            fields = "__all__"

        self.assertEqual(
            list(MyCreateView().get_form_class().base_fields), ["name", "slug"]
        )