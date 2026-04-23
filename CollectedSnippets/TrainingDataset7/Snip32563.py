def test_ipaddress_on_postgresql(self):
        """
        Regression test for #708

        "like" queries on IP address fields require casting with HOST() (on
        PostgreSQL).
        """
        a = Article(name="IP test", text="The body", submitted_from="192.0.2.100")
        a.save()
        self.assertSequenceEqual(
            Article.objects.filter(submitted_from__contains="192.0.2"), [a]
        )
        # The searches do not match the subnet mask (/32 in this case)
        self.assertEqual(
            Article.objects.filter(submitted_from__contains="32").count(), 0
        )