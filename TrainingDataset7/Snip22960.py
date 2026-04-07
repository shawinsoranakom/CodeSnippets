def make_choiceformset(
        self,
        formset_data=None,
        formset_class=ChoiceFormSet,
        total_forms=None,
        initial_forms=0,
        max_num_forms=0,
        min_num_forms=0,
        **kwargs,
    ):
        """
        Make a ChoiceFormset from the given formset_data.
        The data should be given as a list of (choice, votes) tuples.
        """
        kwargs.setdefault("prefix", "choices")
        kwargs.setdefault("auto_id", False)

        if formset_data is None:
            return formset_class(**kwargs)

        if total_forms is None:
            total_forms = len(formset_data)

        def prefixed(*args):
            args = (kwargs["prefix"],) + args
            return "-".join(args)

        data = {
            prefixed("TOTAL_FORMS"): str(total_forms),
            prefixed("INITIAL_FORMS"): str(initial_forms),
            prefixed("MAX_NUM_FORMS"): str(max_num_forms),
            prefixed("MIN_NUM_FORMS"): str(min_num_forms),
        }
        for i, (choice, votes) in enumerate(formset_data):
            data[prefixed(str(i), "choice")] = choice
            data[prefixed(str(i), "votes")] = votes

        return formset_class(data, **kwargs)