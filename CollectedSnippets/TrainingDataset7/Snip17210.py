def test_custom_functions_can_ref_other_functions(self):
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

        class Lower(Func):
            function = "LOWER"

        qs = (
            Company.objects.annotate(
                tagline=Func(
                    F("motto"),
                    F("ticker_name"),
                    F("description"),
                    Value("No Tag"),
                    function="COALESCE",
                )
            )
            .annotate(
                tagline_lower=Lower(F("tagline")),
            )
            .order_by("name")
        )

        # LOWER function supported by:
        # oracle, postgres, mysql, sqlite, sqlserver

        self.assertQuerySetEqual(
            qs,
            [
                ("Apple", "APPL".lower()),
                ("Django Software Foundation", "No Tag".lower()),
                ("Google", "Do No Evil".lower()),
                ("Yahoo", "Internet Company".lower()),
            ],
            lambda c: (c.name, c.tagline_lower),
        )