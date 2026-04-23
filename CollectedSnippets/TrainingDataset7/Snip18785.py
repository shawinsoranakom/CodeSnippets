def test_str(self):
        reference = MockReference("reference", {}, {}, {})
        statement = Statement(
            "%(reference)s - %(non_reference)s",
            reference=reference,
            non_reference="non_reference",
        )
        self.assertEqual(str(statement), "reference - non_reference")