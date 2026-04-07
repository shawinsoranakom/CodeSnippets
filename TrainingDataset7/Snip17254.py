def test_alias_sql_injection(self):
        # RemovedInDjango70Warning: When the deprecation ends, replace with:
        # msg = (
        #    "Column aliases cannot contain whitespace characters, hashes, "
        #    "quotation marks, semicolons, percent signs, or SQL comments."
        # )
        msg = (
            "Column aliases cannot contain whitespace characters, hashes, "
            "control characters, quotation marks, semicolons, or SQL comments."
        )
        for crafted_alias in [
            """injected_name" from "annotations_book"; --""",
            # Control characters.
            *(f"name{chr(c)}" for c in chain(range(32), range(0x7F, 0xA0))),
        ]:
            with self.subTest(crafted_alias):
                with self.assertRaisesMessage(ValueError, msg):
                    Book.objects.alias(**{crafted_alias: Value(1)})