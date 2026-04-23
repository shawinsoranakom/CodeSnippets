def test_callable_called_each_time_form_is_instantiated(self):
        field = StumpJokeForm.base_fields["most_recently_fooled"]
        with mock.patch.object(field, "limit_choices_to") as today_callable_dict:
            StumpJokeForm()
            self.assertEqual(today_callable_dict.call_count, 1)
            StumpJokeForm()
            self.assertEqual(today_callable_dict.call_count, 2)
            StumpJokeForm()
            self.assertEqual(today_callable_dict.call_count, 3)