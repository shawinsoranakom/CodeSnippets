def test_window_frame_repr(self):
        self.assertEqual(
            repr(RowRange(start=-1)),
            "<RowRange: ROWS BETWEEN 1 PRECEDING AND UNBOUNDED FOLLOWING>",
        )
        self.assertEqual(
            repr(ValueRange(start=None, end=1)),
            "<ValueRange: RANGE BETWEEN UNBOUNDED PRECEDING AND 1 FOLLOWING>",
        )
        self.assertEqual(
            repr(ValueRange(start=0, end=0)),
            "<ValueRange: RANGE BETWEEN CURRENT ROW AND CURRENT ROW>",
        )
        self.assertEqual(
            repr(RowRange(start=0, end=0)),
            "<RowRange: ROWS BETWEEN CURRENT ROW AND CURRENT ROW>",
        )
        self.assertEqual(
            repr(RowRange(start=-2, end=-1)),
            "<RowRange: ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING>",
        )
        self.assertEqual(
            repr(RowRange(start=1, end=2)),
            "<RowRange: ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING>",
        )
        self.assertEqual(
            repr(RowRange(start=1, end=2, exclusion=WindowFrameExclusion.CURRENT_ROW)),
            "<RowRange: ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING EXCLUDE CURRENT ROW>",
        )