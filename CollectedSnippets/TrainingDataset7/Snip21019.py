def test_defer_foreign_keys_are_deferred_and_not_traversed(self):
        # select_related() overrides defer().
        with self.assertNumQueries(1):
            obj = Primary.objects.defer("related").select_related()[0]
            self.assert_delayed(obj, 1)
            self.assertEqual(obj.related.id, self.s1.pk)