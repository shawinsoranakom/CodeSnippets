def test_repr_do_not_trigger_validation(self):
        formset = self.make_choiceformset([("test", 1)])
        with mock.patch.object(formset, "full_clean") as mocked_full_clean:
            repr(formset)
            mocked_full_clean.assert_not_called()
            formset.is_valid()
            mocked_full_clean.assert_called()