def test_replace_expressions_transform(self):
        replacements = {F("timestamp"): Value(None)}
        transform_ref = F("timestamp__date")
        self.assertIs(transform_ref.replace_expressions(replacements), transform_ref)
        invalid_transform_ref = F("timestamp__invalid")
        self.assertIs(
            invalid_transform_ref.replace_expressions(replacements),
            invalid_transform_ref,
        )
        replacements = {F("timestamp"): Value(datetime.datetime(2025, 3, 1, 14, 10))}
        self.assertEqual(
            F("timestamp__date").replace_expressions(replacements),
            TruncDate(Value(datetime.datetime(2025, 3, 1, 14, 10))),
        )
        self.assertEqual(
            F("timestamp__date__day").replace_expressions(replacements),
            ExtractDay(TruncDate(Value(datetime.datetime(2025, 3, 1, 14, 10)))),
        )
        invalid_nested_transform_ref = F("timestamp__date__invalid")
        self.assertIs(
            invalid_nested_transform_ref.replace_expressions(replacements),
            invalid_nested_transform_ref,
        )
        # `replacements` is not unnecessarily looked up a second time for
        # transform-less field references as it's the case the vast majority of
        # the time.
        mock_replacements = mock.Mock()
        mock_replacements.get.return_value = None
        field_ref = F("name")
        self.assertIs(field_ref.replace_expressions(mock_replacements), field_ref)
        mock_replacements.get.assert_called_once_with(field_ref)