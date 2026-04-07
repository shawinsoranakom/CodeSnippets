def test_custom_functions(self):
        Company(
            name="Apple",
            motto=None,
            ticker_name="APPL",
            description="Beautiful Devices",
        ).save()
        Company(
            name="Django Software Foundation",
            motto=None,
            ticker_name=None,
            description=None,
        ).save()
        Company(
            name="Google",
            motto="Do No Evil",
            ticker_name="GOOG",
            description="Internet Company",
        ).save()
        Company(
            name="Yahoo", motto=None, ticker_name=None, description="Internet Company"
        ).save()

        qs = Company.objects.annotate(
            tagline=Func(
                F("motto"),
                F("ticker_name"),
                F("description"),
                Value("No Tag"),
                function="COALESCE",
            )
        ).order_by("name")

        self.assertQuerySetEqual(
            qs,
            [
                ("Apple", "APPL"),
                ("Django Software Foundation", "No Tag"),
                ("Google", "Do No Evil"),
                ("Yahoo", "Internet Company"),
            ],
            lambda c: (c.name, c.tagline),
        )