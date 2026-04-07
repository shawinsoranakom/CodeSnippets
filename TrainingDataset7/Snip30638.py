def test_excluded_intermediary_m2m_table_joined(self):
        self.assertSequenceEqual(
            Note.objects.filter(~Q(tag__annotation__name=F("note"))),
            [self.n1, self.n2, self.n3],
        )
        self.assertSequenceEqual(
            Note.objects.filter(tag__annotation__name="a1").filter(
                ~Q(tag__annotation__name=F("note"))
            ),
            [],
        )