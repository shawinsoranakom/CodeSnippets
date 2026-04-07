def test_referenced_base_fields(self):
        # Make sure Q.referenced_base_fields retrieves all base fields from
        # both filters and F expressions.
        tests = [
            (Q(field_1=1) & Q(field_2=1), {"field_1", "field_2"}),
            (
                Q(Exact(F("field_3"), IsNull(F("field_4"), True))),
                {"field_3", "field_4"},
            ),
            (Q(Exact(Q(field_5=F("field_6")), True)), {"field_5", "field_6"}),
            (Q(field_2=1), {"field_2"}),
            (Q(field_7__lookup=True), {"field_7"}),
            (Q(field_7__joined_field__lookup=True), {"field_7"}),
        ]
        combined_q = Q(1)
        combined_q_base_fields = set()
        for q, expected_base_fields in tests:
            combined_q &= q
            combined_q_base_fields |= expected_base_fields
        tests.append((combined_q, combined_q_base_fields))
        for q, expected_base_fields in tests:
            with self.subTest(q=q):
                self.assertEqual(
                    q.referenced_base_fields,
                    expected_base_fields,
                )