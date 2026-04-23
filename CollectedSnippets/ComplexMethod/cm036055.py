def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
        from _pytest.outcomes import Skipped

        # Create a unique temporary file to store exception info from child
        # process. Use test function name and process ID to avoid collisions.
        with (
            tempfile.NamedTemporaryFile(
                delete=False,
                mode="w+b",
                prefix=f"vllm_test_{func.__name__}_{os.getpid()}_",
                suffix=".exc",
            ) as exc_file,
            ExitStack() as delete_after,
        ):
            exc_file_path = exc_file.name
            delete_after.callback(os.remove, exc_file_path)

            pid = os.fork()
            print(f"Fork a new process to run a test {pid}")
            if pid == 0:
                # Make the child process the leader of its own process group
                # to avoid sending SIGTERM to the parent process
                os.setpgrp()
                # Parent process responsible for deleting, don't delete
                # in child.
                delete_after.pop_all()
                try:
                    func(*args, **kwargs)
                except Skipped as e:
                    # convert Skipped to exit code 0
                    print(str(e))
                    os._exit(0)
                except Exception as e:
                    import traceback

                    tb_string = traceback.format_exc()

                    # Try to serialize the exception object first
                    exc_to_serialize: dict[str, Any]
                    try:
                        # First, try to pickle the actual exception with
                        # its traceback.
                        exc_to_serialize = {"pickled_exception": e}
                        # Test if it can be pickled
                        cloudpickle.dumps(exc_to_serialize)
                    except (Exception, KeyboardInterrupt):
                        # Fall back to string-based approach.
                        exc_to_serialize = {
                            "exception_type": type(e).__name__,
                            "exception_msg": str(e),
                            "traceback": tb_string,
                        }
                    try:
                        with open(exc_file_path, "wb") as f:
                            cloudpickle.dump(exc_to_serialize, f)
                    except Exception:
                        # Fallback: just print the traceback.
                        print(tb_string)
                    os._exit(1)
                else:
                    os._exit(0)
            else:
                # After setpgrp(), the child's pgid equals its pid
                pgid = pid
                _pid, _exitcode = os.waitpid(pid, 0)
                # kill all child processes - but they may already have exited cleanly
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(pgid, signal.SIGTERM)
                if _exitcode != 0:
                    # Try to read the exception from the child process
                    exc_info = {}
                    if os.path.exists(exc_file_path):
                        with (
                            contextlib.suppress(Exception),
                            open(exc_file_path, "rb") as f,
                        ):
                            exc_info = cloudpickle.load(f)

                    if (
                        original_exception := exc_info.get("pickled_exception")
                    ) is not None:
                        # Re-raise the actual exception object if it was
                        # successfully pickled.
                        assert isinstance(original_exception, Exception)
                        raise original_exception

                    if (original_tb := exc_info.get("traceback")) is not None:
                        # Use string-based traceback for fallback case
                        raise AssertionError(
                            f"Test {func.__name__} failed when called with"
                            f" args {args} and kwargs {kwargs}"
                            f" (exit code: {_exitcode}):\n{original_tb}"
                        ) from None

                    # Fallback to the original generic error
                    raise AssertionError(
                        f"function {func.__name__} failed when called with"
                        f" args {args} and kwargs {kwargs}"
                        f" (exit code: {_exitcode})"
                    ) from None