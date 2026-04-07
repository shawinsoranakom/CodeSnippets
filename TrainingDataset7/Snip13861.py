def __getstate__(self):
        """
        Make SimpleTestCase picklable for parallel tests using subtests.
        """
        state = super().__dict__
        # _outcome and _subtest cannot be tested on picklability, since they
        # contain the TestCase itself, leading to an infinite recursion.
        if state["_outcome"]:
            pickable_state = {"_outcome": None, "_subtest": None}
            for key, value in state.items():
                if key in pickable_state or not is_pickable(value):
                    continue
                pickable_state[key] = value
            return pickable_state

        return state