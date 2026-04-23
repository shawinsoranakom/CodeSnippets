def to_py_obj(obj):
    """
    Convert a PyTorch tensor, Numpy array or python list to a python list.
    """
    if isinstance(obj, (int, float)):
        return obj
    elif isinstance(obj, (dict, UserDict)):
        return {k: to_py_obj(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        # Only convert directly if all elements are numeric scalars
        if all(isinstance(x, (int, float, np.number)) for x in obj):
            return list(obj)

        # Otherwise recurse element-wise
        return [to_py_obj(o) for o in obj]

    framework_to_py_obj = {
        "pt": lambda obj: obj.tolist(),
        "np": lambda obj: obj.tolist(),
    }

    # This gives us a smart order to test the frameworks with the corresponding tests.
    framework_to_test_func = _get_frameworks_and_test_func(obj)
    for framework, test_func in framework_to_test_func.items():
        if test_func(obj):
            return framework_to_py_obj[framework](obj)

    # tolist also works on 0d np arrays
    if isinstance(obj, np.number):
        return obj.tolist()
    else:
        return obj