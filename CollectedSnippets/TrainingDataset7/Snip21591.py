def test_update_with_join_in_predicate_raise_field_error(self):
        with self.assertRaisesMessage(
            FieldError, "Joined field references are not permitted in this query"
        ):
            CaseTestModel.objects.update(
                string=Case(
                    When(o2o_rel__integer=1, then=Value("one")),
                    When(o2o_rel__integer=2, then=Value("two")),
                    When(o2o_rel__integer=3, then=Value("three")),
                    default=Value("other"),
                ),
            )