def test_expression_signature_uses_deferred_annotations(self):
        class AnnotatedExpression(Expression):
            def __init__(self, *args, my_kw: AnnotatedKwarg, **kwargs):
                super().__init__(*args, **kwargs)

        self.assertEqual(AnnotatedExpression(my_kw=""), AnnotatedExpression(my_kw=""))