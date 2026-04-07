def test_order_by_expression_ref(self):
        self.assertQuerySetEqual(
            Author.objects.annotate(upper_name=Upper("name")).order_by(
                Length("upper_name")
            ),
            Author.objects.order_by(Length(Upper("name"))),
        )