def test_empty_update_fields(self):
        s = Person.objects.create(name="Sara", gender="F")
        pre_save_data = []

        def pre_save_receiver(**kwargs):
            pre_save_data.append(kwargs["update_fields"])

        pre_save.connect(pre_save_receiver)
        post_save_data = []

        def post_save_receiver(**kwargs):
            post_save_data.append(kwargs["update_fields"])

        post_save.connect(post_save_receiver)
        # Save is skipped.
        with self.assertNumQueries(0):
            s.save(update_fields=[])
        # Signals were skipped, too...
        self.assertEqual(len(pre_save_data), 0)
        self.assertEqual(len(post_save_data), 0)

        pre_save.disconnect(pre_save_receiver)
        post_save.disconnect(post_save_receiver)