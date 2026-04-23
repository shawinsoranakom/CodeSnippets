def test_extra_select_alias_sql_injection(self):
        msg = (
            "Column aliases cannot contain whitespace characters, hashes, "
            "control characters, quotation marks, semicolons, or SQL comments."
        )
        for crafted_alias in [
            """injected_name" from "queries_note"; --""",
            # Control characters.
            *(f"name{chr(c)}" for c in chain(range(32), range(0x7F, 0xA0))),
        ]:
            with self.subTest(crafted_alias):
                with self.assertRaisesMessage(ValueError, msg):
                    Note.objects.extra(select={crafted_alias: "1"})