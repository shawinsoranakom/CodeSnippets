def iter_contains(
    items: Iterable[Any],
    search: Any,
    tx: InstructionTranslator,
    check_tensor_identity: bool = False,
) -> Any:
    from .variables import ConstantVariable

    if search.is_python_constant():
        found_const = any(
            x.is_python_constant()
            and x.as_python_constant() == search.as_python_constant()
            for x in items
        )
        return ConstantVariable.create(found_const)

    must_check_tensor_id = False
    if check_tensor_identity and search.is_tensor():
        must_check_tensor_id = True
        # Match of Tensor means match of FakeTensor
        search = _get_fake_tensor(search)

    found: VariableTracker | None = None
    for x in items:
        if must_check_tensor_id:
            if x.is_tensor():
                if search is _get_fake_tensor(x):  # Object equivalence
                    return ConstantVariable.create(True)
        else:
            from torch._dynamo.variables.builder import SourcelessBuilder

            check = SourcelessBuilder.create(tx, operator.eq).call_function(
                tx, [x, search], {}
            )
            if found is None:
                found = check
            else:
                found = SourcelessBuilder.create(tx, operator.or_).call_function(
                    tx, [check, found], {}
                )
    if found is None:
        found = ConstantVariable.create(False)
    return found