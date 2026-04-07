def test_only_when_arguments(self):
        msg = "Positional arguments must all be When objects."
        with self.assertRaisesMessage(TypeError, msg):
            Case(When(Q(pk__in=[])), object())