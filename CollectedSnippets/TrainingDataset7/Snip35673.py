def test_update_fields_signals(self):
        p = Person.objects.create(name="Sara", gender="F")
        pre_save_data = []

        def pre_save_receiver(**kwargs):
            pre_save_data.append(kwargs["update_fields"])

        pre_save.connect(pre_save_receiver)
        post_save_data = []

        def post_save_receiver(**kwargs):
            post_save_data.append(kwargs["update_fields"])

        post_save.connect(post_save_receiver)
        p.save(update_fields=["name"])
        self.assertEqual(len(pre_save_data), 1)
        self.assertEqual(len(pre_save_data[0]), 1)
        self.assertIn("name", pre_save_data[0])
        self.assertEqual(len(post_save_data), 1)
        self.assertEqual(len(post_save_data[0]), 1)
        self.assertIn("name", post_save_data[0])

        pre_save.disconnect(pre_save_receiver)
        post_save.disconnect(post_save_receiver)