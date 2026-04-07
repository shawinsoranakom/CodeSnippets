def test_evaluated_queryset_as_argument(self):
        """
        If a queryset is already evaluated, it can still be used as a query
        arg.
        """
        n = Note(note="Test1", misc="misc")
        n.save()
        e = ExtraInfo(info="good", note=n)
        e.save()

        n_list = Note.objects.all()
        # Evaluate the Note queryset, populating the query cache
        list(n_list)
        # Make one of cached results unpickable.
        n_list._result_cache[0].error = UnpickleableError()
        with self.assertRaises(UnpickleableError):
            pickle.dumps(n_list)
        # Use the note queryset in a query, and evaluate
        # that query in a way that involves cloning.
        self.assertEqual(ExtraInfo.objects.filter(note__in=n_list)[0].info, "good")