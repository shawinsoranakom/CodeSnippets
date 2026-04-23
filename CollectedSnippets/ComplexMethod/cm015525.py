def _are_equal_states(
        self,
        state1: dict[str, Any],
        state2: dict[str, Any],
    ) -> bool:
        """Checks if ``state1`` and ``state2`` contain the same mappings."""
        if set(state1.keys()) != set(state2.keys()):
            return False
        for state_name, value1 in state1.items():
            value2 = state2[state_name]
            if type(value1) is not type(value2):
                return False
            if torch.is_tensor(value1):  # tensor state
                if not torch.is_tensor(value2):
                    raise AssertionError("Expected value2 to be a tensor")
                # Check the values on CPU to be device-agnostic
                value1 = value1.cpu()
                value2 = value2.cpu()
                if value1.shape != value2.shape or not torch.all(
                    torch.isclose(value1, value2)
                ):
                    return False
            else:  # non-tensor state
                if value1 != value2:
                    return False
        return True