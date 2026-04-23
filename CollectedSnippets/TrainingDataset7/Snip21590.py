def test_update_with_join_in_condition_raise_field_error(self):
        with self.assertRaisesMessage(
            FieldError, "Joined field references are not permitted in this query"
        ):
            CaseTestModel.objects.update(
                integer=Case(
                    When(integer2=F("o2o_rel__integer") + 1, then=2),
                    When(integer2=F("o2o_rel__integer"), then=3),
                ),
            )