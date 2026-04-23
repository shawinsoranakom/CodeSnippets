def _validate_example_inputs_for_chain(
    first_example: Example,
    chain: Chain,
    input_mapper: Callable[[dict], Any] | None,
) -> None:
    """Validate that the example inputs match the chain input keys."""
    if input_mapper:
        first_inputs = input_mapper(first_example.inputs or {})
        missing_keys = set(chain.input_keys).difference(first_inputs)
        if not isinstance(first_inputs, dict):
            msg = (
                "When using an input_mapper to prepare dataset example"
                " inputs for a chain, the mapped value must be a dictionary."
                f"\nGot: {first_inputs} of type {type(first_inputs)}."
            )
            raise InputFormatError(msg)
        if missing_keys:
            msg = (
                "Missing keys after loading example using input_mapper."
                f"\nExpected: {chain.input_keys}. Got: {first_inputs.keys()}"
            )
            raise InputFormatError(msg)
    else:
        first_inputs = first_example.inputs or {}
        missing_keys = set(chain.input_keys).difference(first_inputs)
        if len(first_inputs) == 1 and len(chain.input_keys) == 1:
            # We can pass this through the run method.
            # Refrain from calling to validate.
            pass
        elif missing_keys:
            msg = (
                "Example inputs missing expected chain input keys."
                " Please provide an input_mapper to convert the example.inputs"
                " to a compatible format for the chain you wish to evaluate."
                f"Expected: {chain.input_keys}. "
                f"Got: {first_inputs.keys()}"
            )
            raise InputFormatError(msg)