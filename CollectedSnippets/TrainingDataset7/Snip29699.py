def test_check_constraint_daterange_contains(self):
        constraint_name = "dates_contains"
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )
        constraint = CheckConstraint(
            condition=Q(dates__contains=F("dates_inner")),
            name=constraint_name,
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(RangesModel, constraint)
        self.assertIn(constraint_name, self.get_constraints(RangesModel._meta.db_table))
        date_1 = datetime.date(2016, 1, 1)
        date_2 = datetime.date(2016, 1, 4)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RangesModel.objects.create(
                dates=(date_1, date_2),
                dates_inner=(date_1, date_2.replace(day=5)),
            )
        RangesModel.objects.create(
            dates=(date_1, date_2),
            dates_inner=(date_1, date_2),
        )