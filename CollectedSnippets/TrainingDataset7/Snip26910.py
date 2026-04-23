def test_nested_deconstructible_objects(self):
        """
        Nested deconstruction is applied recursively to the args/kwargs of
        deconstructed objects.
        """
        # If the items within a deconstructed object's args/kwargs have the
        # same deconstructed values - whether or not the items themselves are
        # different instances - then the object as a whole is regarded as
        # unchanged.
        changes = self.get_changes(
            [self.author_name_nested_deconstructible_1],
            [self.author_name_nested_deconstructible_2],
        )
        self.assertEqual(changes, {})
        # Differences that exist solely within the args list of a deconstructed
        # object should be reported as changes
        changes = self.get_changes(
            [self.author_name_nested_deconstructible_1],
            [self.author_name_nested_deconstructible_changed_arg],
        )
        self.assertEqual(len(changes), 1)
        # Additional args should also be reported as a change
        changes = self.get_changes(
            [self.author_name_nested_deconstructible_1],
            [self.author_name_nested_deconstructible_extra_arg],
        )
        self.assertEqual(len(changes), 1)
        # Differences that exist solely within the kwargs dict of a
        # deconstructed object should be reported as changes
        changes = self.get_changes(
            [self.author_name_nested_deconstructible_1],
            [self.author_name_nested_deconstructible_changed_kwarg],
        )
        self.assertEqual(len(changes), 1)
        # Additional kwargs should also be reported as a change
        changes = self.get_changes(
            [self.author_name_nested_deconstructible_1],
            [self.author_name_nested_deconstructible_extra_kwarg],
        )
        self.assertEqual(len(changes), 1)