def test_extra_select_literal_percent_s(self):
        # Allow %%s to escape select clauses
        self.assertEqual(Note.objects.extra(select={"foo": "'%%s'"})[0].foo, "%s")
        self.assertEqual(
            Note.objects.extra(select={"foo": "'%%s bar %%s'"})[0].foo, "%s bar %s"
        )
        self.assertEqual(
            Note.objects.extra(select={"foo": "'bar %%s'"})[0].foo, "bar %s"
        )