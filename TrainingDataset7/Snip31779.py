def test_pre_1000ad_date(self):
        """Year values before 1000AD are properly formatted"""
        # Regression for #12524 -- dates before 1000AD get prefixed
        # 0's on the year
        a = Article.objects.create(
            author=self.jane,
            headline="Nobody remembers the early years",
            pub_date=datetime(1, 2, 3, 4, 5, 6),
        )

        serial_str = serializers.serialize(self.serializer_name, [a])
        date_values = self._get_field_values(serial_str, "pub_date")
        self.assertEqual(date_values[0].replace("T", " "), "0001-02-03 04:05:06")