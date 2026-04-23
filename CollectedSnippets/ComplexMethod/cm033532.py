def assert_round_trip(original_value, round_tripped_value, via_copy=False):
    assert original_value == round_tripped_value
    assert AnsibleTagHelper.tags(original_value) == AnsibleTagHelper.tags(round_tripped_value)

    if via_copy and type(original_value) is tuple:  # pylint: disable=unidiomatic-typecheck
        # copy.copy/copy.deepcopy significantly complicate the rules for reference equality with tuple, skip the following checks for values sourced that way
        # tuple impl of __copy__ always returns the same instance, __deepcopy__ always returns the same instance if its contents are immutable
        return

    # singleton values should rehydrate as the shared singleton instance, all others should be a new instance
    if isinstance(original_value, (AnsibleSingletonTagBase, enum.Enum)):
        assert original_value is round_tripped_value
    else:
        assert original_value is not round_tripped_value