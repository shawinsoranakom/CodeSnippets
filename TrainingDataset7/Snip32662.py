def complex_return_value():
    # Return something which isn't JSON serializable nor picklable.
    return lambda: True