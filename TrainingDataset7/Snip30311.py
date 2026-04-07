def test_select_related(self):
        """
        We can still use `select_related()` to include related models in our
        querysets.
        """
        country = Country.objects.create(name="Australia")
        State.objects.create(name="New South Wales", country=country)

        resp = [s.name for s in State.objects.select_related()]
        self.assertEqual(resp, ["New South Wales"])

        resp = [s.name for s in StateProxy.objects.select_related()]
        self.assertEqual(resp, ["New South Wales"])

        self.assertEqual(
            StateProxy.objects.get(name="New South Wales").name, "New South Wales"
        )

        resp = StateProxy.objects.select_related().get(name="New South Wales")
        self.assertEqual(resp.name, "New South Wales")