def test_order_by_grandparent_fk_with_expression_in_default_ordering(self):
        p3 = OrderedByExpression.objects.create(name="oBJ 3")
        p2 = OrderedByExpression.objects.create(name="OBJ 2")
        p1 = OrderedByExpression.objects.create(name="obj 1")
        c3 = OrderedByExpressionChild.objects.create(parent=p3)
        c2 = OrderedByExpressionChild.objects.create(parent=p2)
        c1 = OrderedByExpressionChild.objects.create(parent=p1)
        g3 = OrderedByExpressionGrandChild.objects.create(parent=c3)
        g2 = OrderedByExpressionGrandChild.objects.create(parent=c2)
        g1 = OrderedByExpressionGrandChild.objects.create(parent=c1)
        self.assertSequenceEqual(
            OrderedByExpressionGrandChild.objects.order_by("parent"),
            [g1, g2, g3],
        )