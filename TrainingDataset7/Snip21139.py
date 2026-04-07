def test_fast_delete_empty_no_update_can_self_select(self):
        """
        Fast deleting when DatabaseFeatures.update_can_self_select = False
        works even if the specified filter doesn't match any row (#25932).
        """
        with self.assertNumQueries(1):
            self.assertEqual(
                User.objects.filter(avatar__desc="missing").delete(),
                (0, {}),
            )