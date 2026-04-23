def test_ticket9985(self):
        # qs.values_list(...).values(...) combinations should work.
        self.assertSequenceEqual(
            Note.objects.values_list("note", flat=True).values("id").order_by("id"),
            [{"id": 1}, {"id": 2}, {"id": 3}],
        )
        self.assertSequenceEqual(
            Annotation.objects.filter(
                notes__in=Note.objects.filter(note="n1")
                .values_list("note")
                .values("id")
            ),
            [self.ann1],
        )