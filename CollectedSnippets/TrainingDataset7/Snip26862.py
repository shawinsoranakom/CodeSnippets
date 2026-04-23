def test_empty_unique_together(self):
        """Empty unique_together shouldn't generate a migration."""
        # Explicitly testing for not specified, since this is the case after
        # a CreateModel operation w/o any definition on the original model
        model_state_not_specified = ModelState(
            "a", "model", [("id", models.AutoField(primary_key=True))]
        )
        # Explicitly testing for None, since this was the issue in #23452 after
        # an AlterUniqueTogether operation with e.g. () as value
        model_state_none = ModelState(
            "a",
            "model",
            [("id", models.AutoField(primary_key=True))],
            {
                "unique_together": None,
            },
        )
        # Explicitly testing for the empty set, since we now always have sets.
        # During removal (('col1', 'col2'),) --> () this becomes set([])
        model_state_empty = ModelState(
            "a",
            "model",
            [("id", models.AutoField(primary_key=True))],
            {
                "unique_together": set(),
            },
        )

        def test(from_state, to_state, msg):
            changes = self.get_changes([from_state], [to_state])
            if changes:
                ops = ", ".join(
                    o.__class__.__name__ for o in changes["a"][0].operations
                )
                self.fail("Created operation(s) %s from %s" % (ops, msg))

        tests = (
            (
                model_state_not_specified,
                model_state_not_specified,
                '"not specified" to "not specified"',
            ),
            (model_state_not_specified, model_state_none, '"not specified" to "None"'),
            (
                model_state_not_specified,
                model_state_empty,
                '"not specified" to "empty"',
            ),
            (model_state_none, model_state_not_specified, '"None" to "not specified"'),
            (model_state_none, model_state_none, '"None" to "None"'),
            (model_state_none, model_state_empty, '"None" to "empty"'),
            (
                model_state_empty,
                model_state_not_specified,
                '"empty" to "not specified"',
            ),
            (model_state_empty, model_state_none, '"empty" to "None"'),
            (model_state_empty, model_state_empty, '"empty" to "empty"'),
        )

        for t in tests:
            test(*t)