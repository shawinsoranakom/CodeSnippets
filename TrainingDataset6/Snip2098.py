def match(command):
    failed_lifecycle = _get_failed_lifecycle(command)
    available_lifecycles = _getavailable_lifecycles(command)
    return available_lifecycles and failed_lifecycle