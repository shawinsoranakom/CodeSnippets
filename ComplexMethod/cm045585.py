def wait_for_process_handles(
    process_handles: list[subprocess.Popen],
    timeout: float,
) -> ProcessHandlesState:
    result = ProcessHandlesState()
    for _ in range(2):
        # A process may finish by requesting scaling, but do so after we have already
        # checked its exit status. At the same time, another process may terminate with
        # exit code 1, indicating a failure to communicate with the process that requested
        # scaling. In that case, only the latter exit code would be observed, causing the
        # program to terminate due to an error.
        #
        # To prevent this, once an error is detected, we must first verify that no scaling
        # request was issued by the second pass.

        for handle in process_handles:
            try:
                maybe_exit_code = handle.wait(timeout)
            except subprocess.TimeoutExpired:
                result.has_working_process = True
                continue
            if maybe_exit_code == EXIT_CODE_DOWNSCALE:
                result.needs_downscaling = True
            elif maybe_exit_code == EXIT_CODE_UPSCALE:
                result.needs_upscaling = True
            elif maybe_exit_code != 0:
                result.has_process_with_error = True

        if not result.has_process_with_error:
            # If there is no process with an error, then a retry described above is redundant
            # and can be avoided.
            break

    return result