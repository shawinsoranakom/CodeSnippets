def _check_if_instances_equal(op1, op2) -> bool:
    """
    Utility function to check if two instances of a class are equal.
    """
    # cutlass uses list and tuple inconsistently
    if isinstance(op1, (list | tuple)):
        return tuple(op1) == tuple(op2)

    if type(op1) is not type(op2):
        return False

    # some classes have __eq__ defined but they may be insufficient
    if op1.__class__.__dict__.get("__eq__") and op1 != op2:
        return False

    if isinstance(op1, Enum):
        return op1.value == op2.value

    if hasattr(op1, "__dict__"):
        for key, value in op1.__dict__.items():
            if key not in op2.__dict__:
                return False
            if not _check_if_instances_equal(value, op2.__dict__[key]):
                return False

    return True