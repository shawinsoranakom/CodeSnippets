def test_opclass_func_validate_constraints(self):
        constraint_name = "test_opclass_func_validate_constraints"
        constraint = UniqueConstraint(
            OpClass(Lower("scene"), name="text_pattern_ops"),
            name="test_opclass_func_validate_constraints",
        )
        Scene.objects.create(scene="First scene")
        # Non-unique scene.
        msg = f"Constraint “{constraint_name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(Scene, Scene(scene="first Scene"))
        constraint.validate(Scene, Scene(scene="second Scene"))