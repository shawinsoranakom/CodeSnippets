def test_order_by_rawsql(self):
        self.assertSequenceEqual(
            Item.objects.values("note__note").order_by(
                RawSQL("queries_note.note", ()),
                "id",
            ),
            [
                {"note__note": "n2"},
                {"note__note": "n3"},
                {"note__note": "n3"},
                {"note__note": "n3"},
            ],
        )