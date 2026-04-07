def test_values_expression_alias_sql_injection_json_field(self):
        msg = (
            "Column aliases cannot contain whitespace characters, hashes, "
            "control characters, quotation marks, semicolons, or SQL comments."
        )
        for crafted_alias in [
            """injected_name" from "expressions_company"; --""",
            # Control characters.
            *(chr(c) for c in chain(range(32), range(0x7F, 0xA0))),
        ]:
            with self.subTest(crafted_alias):
                with self.assertRaisesMessage(ValueError, msg):
                    JSONFieldModel.objects.values(f"data__{crafted_alias}")

                with self.assertRaisesMessage(ValueError, msg):
                    JSONFieldModel.objects.values_list(f"data__{crafted_alias}")