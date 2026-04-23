def test_view_not_found_message(self):
        msg = (
            "Reverse for 'nonexistent-view' not found. 'nonexistent-view' "
            "is not a valid view function or pattern name."
        )
        with self.assertRaisesMessage(NoReverseMatch, msg):
            reverse("nonexistent-view")