def test_hash(self):
        expression_1 = Case(
            When(account_type__in=[Client.REGULAR, Client.GOLD], then=1),
            default=2,
            output_field=IntegerField(),
        )
        expression_2 = Case(
            When(account_type__in=(Client.REGULAR, Client.GOLD), then=1),
            default=2,
            output_field=IntegerField(),
        )
        expression_3 = Case(
            When(account_type__in=[Client.REGULAR, Client.GOLD], then=1), default=2
        )
        expression_4 = Case(
            When(account_type__in=[Client.PLATINUM, Client.GOLD], then=2), default=1
        )
        self.assertEqual(hash(expression_1), hash(expression_2))
        self.assertNotEqual(hash(expression_2), hash(expression_3))
        self.assertNotEqual(hash(expression_1), hash(expression_4))
        self.assertNotEqual(hash(expression_3), hash(expression_4))