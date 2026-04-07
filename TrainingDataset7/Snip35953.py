def test_mutually_exclusive_group_required_with_same_dest_options(self):
        tests = [
            {"until": "2"},
            {"for": "1", "until": "2"},
        ]
        msg = (
            "Cannot pass the dest 'until' that matches multiple arguments via "
            "**options."
        )
        for options in tests:
            with self.subTest(options=options):
                with self.assertRaisesMessage(TypeError, msg):
                    management.call_command(
                        "mutually_exclusive_required_with_same_dest",
                        **options,
                    )