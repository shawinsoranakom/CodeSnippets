def test_maxdiff(self):
        names = ["Joe Smith %s" % i for i in range(20)]
        Person.objects.bulk_create([Person(name=name) for name in names])
        names.append("Extra Person")

        with self.assertRaises(AssertionError) as ctx:
            self.assertQuerySetEqual(
                Person.objects.filter(name__startswith="Joe"),
                names,
                ordered=False,
                transform=lambda p: p.name,
            )
        self.assertIn("Set self.maxDiff to None to see it.", str(ctx.exception))

        original = self.maxDiff
        self.maxDiff = None
        try:
            with self.assertRaises(AssertionError) as ctx:
                self.assertQuerySetEqual(
                    Person.objects.filter(name__startswith="Joe"),
                    names,
                    ordered=False,
                    transform=lambda p: p.name,
                )
        finally:
            self.maxDiff = original
        exception_msg = str(ctx.exception)
        self.assertNotIn("Set self.maxDiff to None to see it.", exception_msg)
        for name in names:
            self.assertIn(name, exception_msg)