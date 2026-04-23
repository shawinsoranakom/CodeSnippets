def on_change(
            self, key: pw.Pointer, row: dict[str, Any], time: int, is_addition: bool
        ) -> None:
            self.n_rows_processed += 1
            assert row["a"] == "foo"
            assert row["b"] == 1.5
            assert not row["c"]
            assert row["d"] == (1, 2, 3)
            assert row["e"] == (1, 2, 3)
            assert row["f"] == pw.Json({"foo": "bar", "baz": 123})
            assert row["g"] == datetime.datetime(2025, 3, 14, 10, 13)
            assert row["h"] == datetime.datetime(
                2025, 4, 23, 10, 13, tzinfo=datetime.timezone.utc
            )
            assert row["i"].value == SimpleObject("test")
            assert row["j"] == pd.Timedelta("4 days 2 seconds 123 us")
            assert row["k"] == ("abc", "def", "ghi")
            assert row["l"] == (
                pd.Timedelta("4 days 2 seconds 123 us"),
                pd.Timedelta("1 days 2 seconds 3 us"),
            )
            assert row["m"] == (("a", "b"), ("c", "d"))