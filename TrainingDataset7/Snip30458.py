def test_replace_expressions(self):
        replacements = {F("timestamp"): Value(None)}
        self.assertEqual(
            Q(timestamp__date__day=25).replace_expressions(replacements),
            Q(timestamp__date__day=25),
        )
        replacements = {F("timestamp"): Value(datetime(2025, 10, 23))}
        self.assertEqual(
            Q(timestamp__date__day=13).replace_expressions(replacements),
            Q(
                IntegerFieldExact(
                    ExtractDay(TruncDate(Value(datetime(2025, 10, 23)))),
                    13,
                )
            ),
        )
        self.assertEqual(
            Q(timestamp__date__day__lte=25).replace_expressions(replacements),
            Q(
                IntegerLessThanOrEqual(
                    ExtractDay(TruncDate(Value(datetime(2025, 10, 23)))),
                    25,
                )
            ),
        )
        self.assertEqual(
            (
                Q(Q(timestamp__date__day__lte=25), timestamp__date__day=13)
            ).replace_expressions(replacements),
            (
                Q(
                    Q(
                        IntegerLessThanOrEqual(
                            ExtractDay(TruncDate(Value(datetime(2025, 10, 23)))),
                            25,
                        )
                    ),
                    IntegerFieldExact(
                        ExtractDay(TruncDate(Value(datetime(2025, 10, 23)))),
                        13,
                    ),
                )
            ),
        )
        self.assertEqual(
            Q(timestamp=None).replace_expressions(replacements),
            Q(IsNull(Value(datetime(2025, 10, 23)), True)),
        )
        self.assertEqual(
            Q(timestamp__date__day__invalid=25).replace_expressions(replacements),
            Q(timestamp__date__day__invalid=25),
        )