def test_multiple_foreignkeys(self):
        # Test of multiple ForeignKeys to the same model (bug #7125).
        c1 = Category.objects.create(name="First")
        c2 = Category.objects.create(name="Second")
        c3 = Category.objects.create(name="Third")
        r1 = Record.objects.create(category=c1)
        r2 = Record.objects.create(category=c1)
        r3 = Record.objects.create(category=c2)
        r4 = Record.objects.create(category=c2)
        r5 = Record.objects.create(category=c3)
        Relation.objects.create(left=r1, right=r2)
        Relation.objects.create(left=r3, right=r4)
        rel = Relation.objects.create(left=r1, right=r3)
        Relation.objects.create(left=r5, right=r2)
        Relation.objects.create(left=r3, right=r2)

        q1 = Relation.objects.filter(
            left__category__name__in=["First"], right__category__name__in=["Second"]
        )
        self.assertSequenceEqual(q1, [rel])

        q2 = Category.objects.filter(
            record__left_set__right__category__name="Second"
        ).order_by("name")
        self.assertSequenceEqual(q2, [c1, c2])

        p = Parent.objects.create(name="Parent")
        c = Child.objects.create(name="Child", parent=p)
        msg = 'Cannot assign "%r": "Child.parent" must be a "Parent" instance.' % c
        with self.assertRaisesMessage(ValueError, msg):
            Child.objects.create(name="Grandchild", parent=c)