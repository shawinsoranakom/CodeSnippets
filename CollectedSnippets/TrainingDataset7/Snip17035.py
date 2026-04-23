def test_alias_sql_injection(self):
        msg = (
            "Column aliases cannot contain whitespace characters, hashes, "
            "control characters, quotation marks, semicolons, or SQL comments."
        )
        for crafted_alias in [
            """injected_name" from "aggregation_author"; --""",
            # Control characters.
            *(f"name{chr(c)}" for c in chain(range(32), range(0x7F, 0xA0))),
        ]:
            with self.subTest(crafted_alias):
                with self.assertRaisesMessage(ValueError, msg):
                    Author.objects.aggregate(**{crafted_alias: Avg("age")})