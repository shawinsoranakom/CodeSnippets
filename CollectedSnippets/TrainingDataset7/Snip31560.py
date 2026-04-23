def test_ordered_select_for_update(self):
        """
        Subqueries should respect ordering as an ORDER BY clause may be useful
        to specify a row locking order to prevent deadlocks (#27193).
        """
        with transaction.atomic():
            qs = Person.objects.filter(
                id__in=Person.objects.order_by("-id").select_for_update()
            )
            self.assertIn("ORDER BY", str(qs.query))