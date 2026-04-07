def test_empty_string_is_null(self):
        p = Poll.objects.create(question="?")
        c1 = Choice.objects.create(poll=p, choice=None)
        c2 = Choice.objects.create(poll=p, choice="")
        cases = [{"choice__exact": ""}, {"choice__iexact": ""}]
        for lookup in cases:
            with self.subTest(lookup):
                self.assertSequenceEqual(
                    Choice.objects.filter(**lookup).order_by("id"), [c1, c2]
                )