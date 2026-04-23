def test_not_implemented_error_on_missing_iter(self):
        class InvalidChoiceIterator(BaseChoiceIterator):
            pass  # Not overriding __iter__().

        msg = "BaseChoiceIterator subclasses must implement __iter__()."
        with self.assertRaisesMessage(NotImplementedError, msg):
            iter(InvalidChoiceIterator())