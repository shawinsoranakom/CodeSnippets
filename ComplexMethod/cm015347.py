def verify_reusing_compiled_graph(mod, exception_msg_pattern, ncase=10):
    args = gen_rand_args(mod)
    mod(*args)

    dis.dis(mod.forward)

    try:
        optimized_mod = extract_compiled_graph(fx.symbolic_trace(mod), args)
    except RuntimeError as e:
        if exception_msg_pattern is None:
            raise e  # reraise the exception
        exception_message = str(e)
        if not re.search(exception_msg_pattern, exception_message):
            raise RuntimeError(
                f"Exception message does not match the required pattern: {exception_message}"
            ) from e
        else:
            # We are done for the test case that expects an exception
            return

    if exception_msg_pattern is not None:
        raise RuntimeError(
            f"Expect an exception matching pattern {exception_msg_pattern}"
        )
    print("return value of optimized_mod", optimized_mod(*args))

    # check correctness
    failed_index = []
    for i in range(ncase):
        rand_args = gen_rand_args(mod)
        rand_args_copy = copy.deepcopy(rand_args)
        expected = mod(*rand_args)
        actual = optimized_mod(*rand_args_copy)

        if not allclose(expected, actual):
            print(f"Incorrect results. expected {expected}, actual {actual}")
            failed_index.append(i)
            continue

        # make sure arguments match after calling the model forward method to handle inplace
        # updates.
        if not allclose(rand_args, rand_args_copy):
            print(
                f"Incorrect updated arguments. expected {rand_args}, actual {rand_args_copy}"
            )
            failed_index.append(i)
            continue

    if len(failed_index) > 0:
        raise RuntimeError(f"Failed {len(failed_index)}/{ncase} cases")