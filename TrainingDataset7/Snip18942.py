def test_manager_method_signature(self):
        self.assertEqual(
            str(inspect.signature(Article.objects.bulk_create)),
            "(objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, "
            "update_fields=None, unique_fields=None)",
        )