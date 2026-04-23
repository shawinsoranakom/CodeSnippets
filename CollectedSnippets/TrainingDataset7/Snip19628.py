def test_filter_case_when(self):
        msg = "When expression does not support composite primary keys."
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.filter(text=Case(When(text="", then="pk")))
        msg = "Case expression does not support composite primary keys."
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.filter(text=Case(When(text="", then="text"), default="pk"))