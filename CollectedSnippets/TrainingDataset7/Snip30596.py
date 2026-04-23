def test_ticket4358(self):
        # If you don't pass any fields to values(), relation fields are
        # returned as "foo_id" keys, not "foo". For consistency, you should be
        # able to pass "foo_id" in the fields list and have it work, too. We
        # actually allow both "foo" and "foo_id".
        # The *_id version is returned by default.
        self.assertIn("note_id", ExtraInfo.objects.values()[0])
        # You can also pass it in explicitly.
        self.assertSequenceEqual(
            ExtraInfo.objects.values("note_id"), [{"note_id": 1}, {"note_id": 2}]
        )
        # ...or use the field name.
        self.assertSequenceEqual(
            ExtraInfo.objects.values("note"), [{"note": 1}, {"note": 2}]
        )