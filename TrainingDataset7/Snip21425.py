def test_equal(self):
        self.assertEqual(Expression(), Expression())
        self.assertEqual(
            Expression(IntegerField()), Expression(output_field=IntegerField())
        )
        self.assertEqual(Expression(IntegerField()), mock.ANY)
        self.assertNotEqual(Expression(IntegerField()), Expression(CharField()))

        class TestModel(Model):
            field = IntegerField()
            other_field = IntegerField()

        self.assertNotEqual(
            Expression(TestModel._meta.get_field("field")),
            Expression(TestModel._meta.get_field("other_field")),
        )

        class InitCaptureExpression(Expression):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        # The identity of expressions that obscure their __init__() signature
        # with *args and **kwargs cannot be determined when bound with
        # different combinations or *args and **kwargs.
        self.assertNotEqual(
            InitCaptureExpression(IntegerField()),
            InitCaptureExpression(output_field=IntegerField()),
        )

        # However, they should be considered equal when their bindings are
        # equal.
        self.assertEqual(
            InitCaptureExpression(IntegerField()),
            InitCaptureExpression(IntegerField()),
        )
        self.assertEqual(
            InitCaptureExpression(output_field=IntegerField()),
            InitCaptureExpression(output_field=IntegerField()),
        )