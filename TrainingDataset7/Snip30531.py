def test_order_raises_on_non_selected_column(self):
        qs1 = (
            Number.objects.filter()
            .annotate(
                annotation=Value(1, IntegerField()),
            )
            .values("annotation", num2=F("num"))
        )
        qs2 = Number.objects.filter().values("id", "num")
        # Should not raise
        list(qs1.union(qs2).order_by("annotation"))
        list(qs1.union(qs2).order_by("num2"))
        msg = "ORDER BY term does not match any column in the result set"
        # 'id' is not part of the select
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.union(qs2).order_by("id"))
        # 'num' got realiased to num2
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.union(qs2).order_by("num"))
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.union(qs2).order_by(F("num")))
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.union(qs2).order_by(F("num").desc()))
        # switched order, now 'exists' again:
        list(qs2.union(qs1).order_by("num"))