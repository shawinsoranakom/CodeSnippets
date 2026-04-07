def test_limit_choices_to_callable_for_fk_rel(self):
        """
        A ForeignKey can use limit_choices_to as a callable (#2554).
        """
        stumpjokeform = StumpJokeForm()
        self.assertSequenceEqual(
            stumpjokeform.fields["most_recently_fooled"].queryset, [self.threepwood]
        )