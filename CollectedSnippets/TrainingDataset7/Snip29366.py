def test_order_by_parent_fk_with_expression_in_default_ordering(self):
        p3 = OrderedByExpression.objects.create(name="oBJ 3")
        p2 = OrderedByExpression.objects.create(name="OBJ 2")
        p1 = OrderedByExpression.objects.create(name="obj 1")
        c3 = OrderedByExpressionChild.objects.create(parent=p3)
        c2 = OrderedByExpressionChild.objects.create(parent=p2)
        c1 = OrderedByExpressionChild.objects.create(parent=p1)
        self.assertSequenceEqual(
            OrderedByExpressionChild.objects.order_by("parent"),
            [c1, c2, c3],
        )