def sensitive_args_function(sauce):
    # Do not just use plain strings for the variables' values in the code
    # so that the tests don't return false positives when the function's source
    # is displayed in the exception report.
    cooked_eggs = "".join(["s", "c", "r", "a", "m", "b", "l", "e", "d"])  # NOQA
    raise Exception