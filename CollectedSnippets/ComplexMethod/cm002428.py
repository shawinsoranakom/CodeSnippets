def _patched_tearDown(self, *args, **kwargs):
    """Used to report a test that has failures captured and handled by patched functions/methods (without re-raise).

    The patched functions/methods refer to the `patched` defined in `_patch_with_call_info`, which is applied to
    `torch.testing.assert_close` and `unittest.case.TestCase.assertEqual`.

    The objective is to avoid a failure being silence after being processed.

    If there is any failure that is not handled by the patched functions/methods, we add custom error message for them
    along with the usual pytest failure report.
    """

    # Check for regular failures before clearing:
    # when `_patched_tearDown` is called, the current test fails due to an assertion error given by a method being
    # patched by `_patch_with_call_info`. The patched method catches such an error and continue running the remaining
    # statements within the test. If the test fails with another error not handled by the patched methods, we don't let
    # pytest to fail and report it but the original failure (the first one that was processed) instead.
    # We still record those failures not handled by the patched methods, and add custom messages along with the usual
    # pytest failure report.
    regular_failures_info = []

    errors = None
    if hasattr(self._outcome, "errors"):
        errors = self._outcome.errors
    elif hasattr(self._outcome, "result") and hasattr(self._outcome.result, "errors"):
        errors = self._outcome.result.errors

    if hasattr(self, "_outcome") and errors:
        for error_entry in errors:
            test_instance, (exc_type, exc_obj, exc_tb) = error_entry
            # breakpoint()
            regular_failures_info.append(
                {
                    "message": f"{str(exc_obj)}\n\n",
                    "type": exc_type.__name__,
                    "file": "test_modeling_vit.py",
                    "line": 237,  # get_deepest_frame_line(exc_tb)  # Your helper function
                }
            )

        # Clear the regular failure (i.e. that is not from any of our patched assertion methods) from pytest's records.
        if hasattr(self._outcome, "errors"):
            self._outcome.errors.clear()
        elif hasattr(self._outcome, "result") and hasattr(self._outcome.result, "errors"):
            self._outcome.result.errors.clear()

    # reset back to the original tearDown method, so `_patched_tearDown` won't be run by the subsequent tests if they
    # have only test failures that are not handle by the patched methods (or no test failure at all).
    orig_tearDown = _patched_tearDown.orig_tearDown
    type(self).tearDown = orig_tearDown

    # Call the original tearDown
    orig_tearDown(self, *args, **kwargs)

    # Get the failure
    test_method = getattr(self, self._testMethodName)
    captured_failures = test_method.__func__.captured_failures[id(test_method)]

    # TODO: How could we show several exceptions in a sinigle test on the terminal? (Maybe not a good idea)
    captured_exceptions = captured_failures[0]["exception"]
    captured_traceback = captured_failures[0]["traceback"]
    # Show the captured information on the terminal.
    capturued_info = [x["info"] for x in captured_failures]
    capturued_info_str = f"\n\n{'=' * 80}\n\n".join(capturued_info)

    # Enhance the exception message if there were suppressed failures
    if regular_failures_info:
        enhanced_message = f"""{str(captured_exceptions)}

{"=" * 80}
Handled Failures: ({len(capturued_info)} handled):
{"-" * 80}\n
{capturued_info_str}

{"=" * 80}
Unhandled Failures: ({len(regular_failures_info)} unhandled):
{"-" * 80}\n
{", ".join(f"{info['type']}: {info['message']}{info['file']}:{info['line']}" for info in regular_failures_info)}

{"-" * 80}
Note: This failure occurred after other failures analyzed by the patched assertion methods.
To see the full details, temporarily disable assertion patching.
{"=" * 80}"""

        # Create new exception with enhanced message
        enhanced_exception = type(captured_exceptions)(enhanced_message)
        enhanced_exception.__cause__ = captured_exceptions.__cause__
        enhanced_exception.__context__ = captured_exceptions.__context__

        # Raise with your existing traceback reconstruction
        captured_exceptions = enhanced_exception

    # clean up the recorded status
    del test_method.__func__.captured_failures

    raise captured_exceptions.with_traceback(captured_traceback)