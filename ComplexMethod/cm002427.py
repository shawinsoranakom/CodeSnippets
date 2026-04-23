def _get_test_info():
    """
    Collect some information about the current test.

    For example, test full name, line number, stack, traceback, etc.
    """

    full_test_name = os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0]
    test_file, test_class, test_name = full_test_name.split("::")

    # from the most recent frame to the top frame
    stack_from_inspect = inspect.stack()
    # but visit from the top frame to the most recent frame

    actual_test_file, _actual_test_class = test_file, test_class
    test_frame, test_obj, test_method = None, None, None
    for frame in reversed(stack_from_inspect):
        # if test_file in str(frame).replace(r"\\", "/"):
        # check frame's function + if it has `self` as locals; double check if self has the (function) name
        # TODO: Question: How about expanded?
        if (
            test_name.startswith(frame.function)
            and "self" in frame.frame.f_locals
            and hasattr(frame.frame.f_locals["self"], test_name)
        ):
            # if test_name == frame.frame.f_locals["self"]._testMethodName:
            test_frame = frame
            # The test instance
            test_obj = frame.frame.f_locals["self"]
            # TODO: Do we get the (relative?) path or it's just a file name?
            # TODO: Does `test_obj` always have `tearDown` object?
            actual_test_file = frame.filename
            # TODO: check `test_method` will work used at the several places!
            test_method = getattr(test_obj, test_name)
            break

    if test_frame is not None:
        line_number = test_frame.lineno

    # The frame of `patched` being called (the one and the only one calling `_get_test_info`)
    # This is used to get the original method being patched in order to get the context.
    frame_of_patched_obj = None

    captured_frames = []
    to_capture = False
    # From the most outer (i.e. python's `runpy.py`) frame to most inner frame (i.e. the frame of this method)
    # Between `the test method being called` and `before entering `patched``.
    for frame in reversed(stack_from_inspect):
        if (
            test_name.startswith(frame.function)
            and "self" in frame.frame.f_locals
            and hasattr(frame.frame.f_locals["self"], test_name)
        ):
            to_capture = True
        # TODO: check simply with the name is not robust.
        elif frame.frame.f_code.co_name == "patched":
            frame_of_patched_obj = frame
            to_capture = False
            break
        if to_capture:
            captured_frames.append(frame)

    tb_next = None
    for frame_info in reversed(captured_frames):
        tb = types.TracebackType(tb_next, frame_info.frame, frame_info.frame.f_lasti, frame_info.frame.f_lineno)
        tb_next = tb
    test_traceback = tb

    origin_method_being_patched = frame_of_patched_obj.frame.f_locals["orig_method"]

    # An iterable of type `traceback.StackSummary` with each element of type `FrameSummary`
    stack = traceback.extract_stack()
    # The frame which calls `the original method being patched`
    caller_frame = None
    # From the most inner (i.e. recent) frame to the most outer frame
    for frame in reversed(stack):
        if origin_method_being_patched.__name__ in frame.line:
            caller_frame = frame

    caller_path = os.path.relpath(caller_frame.filename)
    caller_lineno = caller_frame.lineno

    test_lineno = line_number

    # Get the code context in the test function/method.
    from _pytest._code.source import Source

    with open(actual_test_file) as fp:
        s = fp.read()
        source = Source(s)
        test_code_context = "\n".join(source.getstatement(test_lineno - 1).lines)

    # Get the code context in the caller (to the patched function/method).
    with open(caller_path) as fp:
        s = fp.read()
        source = Source(s)
        caller_code_context = "\n".join(source.getstatement(caller_lineno - 1).lines)

    test_info = f"test:\n\n{full_test_name}\n\n{'-' * 80}\n\ntest context: {actual_test_file}:{test_lineno}\n\n{test_code_context}"
    test_info = f"{test_info}\n\n{'-' * 80}\n\ncaller context: {caller_path}:{caller_lineno}\n\n{caller_code_context}"

    return (
        full_test_name,
        test_file,
        test_lineno,
        test_obj,
        test_method,
        test_frame,
        test_traceback,
        test_code_context,
        caller_path,
        caller_lineno,
        caller_code_context,
        test_info,
    )