def test_none_as_null(self):
        """
        Regression test for the use of None as a query value.

        None is interpreted as an SQL NULL, but only in __exact and __iexact
        queries.
        Set up some initial polls and choices
        """
        p1 = Poll(question="Why?")
        p1.save()
        c1 = Choice(poll=p1, choice="Because.")
        c1.save()
        c2 = Choice(poll=p1, choice="Why Not?")
        c2.save()

        # Exact query with value None returns nothing ("is NULL" in sql,
        # but every 'id' field has a value).
        self.assertSequenceEqual(Choice.objects.filter(choice__exact=None), [])

        # The same behavior for iexact query.
        self.assertSequenceEqual(Choice.objects.filter(choice__iexact=None), [])

        # Excluding the previous result returns everything.
        self.assertSequenceEqual(
            Choice.objects.exclude(choice=None).order_by("id"), [c1, c2]
        )

        # Valid query, but fails because foo isn't a keyword
        msg = (
            "Cannot resolve keyword 'foo' into field. Choices are: choice, id, poll, "
            "poll_id"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Choice.objects.filter(foo__exact=None)

        # Can't use None on anything other than __exact and __iexact
        with self.assertRaisesMessage(ValueError, "Cannot use None as a query value"):
            Choice.objects.filter(id__gt=None)