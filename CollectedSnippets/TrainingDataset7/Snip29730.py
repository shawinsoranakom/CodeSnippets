def test_validate_generated_field_range_adjacent(self):
        class RangesModelGeneratedField(Model):
            ints = IntegerRangeField(blank=True, null=True)
            ints_generated = GeneratedField(
                expression=F("ints"),
                output_field=IntegerRangeField(null=True),
                db_persist=True,
            )

        with connection.schema_editor() as editor:
            editor.create_model(RangesModelGeneratedField)

        constraint = ExclusionConstraint(
            name="ints_adjacent",
            expressions=[("ints_generated", RangeOperators.ADJACENT_TO)],
            violation_error_code="custom_code",
            violation_error_message="Custom error message.",
        )
        RangesModelGeneratedField.objects.create(ints=(20, 50))

        range_obj = RangesModelGeneratedField(ints=(3, 20))
        with self.assertRaisesMessage(ValidationError, "Custom error message."):
            constraint.validate(RangesModelGeneratedField, range_obj)

        # Excluding referenced or generated field should skip validation.
        constraint.validate(RangesModelGeneratedField, range_obj, exclude={"ints"})
        constraint.validate(
            RangesModelGeneratedField, range_obj, exclude={"ints_generated"}
        )