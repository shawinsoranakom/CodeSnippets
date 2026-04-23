def _do_until_success_or_condition(
    task_action: str,
    connection: ConnectionBase,
    host_context: t.Dict[str, t.Any],
    action_desc: str,
    condition: t.Callable[[int], bool],
    func: t.Callable[..., T],
    *args: t.Any,
    **kwargs: t.Any,
) -> t.Optional[T]:
    """Runs the function multiple times ignoring errors until the condition is false"""
    fail_count = 0
    max_fail_sleep = 12
    reset_required = False
    last_error = None

    while fail_count == 0 or condition(fail_count):
        try:
            if reset_required:
                # Keep on trying the reset until it succeeds.
                _reset_connection(task_action, connection, host_context)
                reset_required = False

            else:
                res = func(*args, **kwargs)
                display.vvvvv("%s: %s success" % (task_action, action_desc))

                return res

        except Exception as e:
            last_error = e

            if not isinstance(e, _TestCommandFailure):
                # The error may be due to a connection problem, just reset the connection just in case
                reset_required = True

            # Use exponential backoff with a max timeout, plus a little bit of randomness
            random_int = random.randint(0, 1000) / 1000
            fail_sleep = 2**fail_count + random_int
            if fail_sleep > max_fail_sleep:
                fail_sleep = max_fail_sleep + random_int

            try:
                error = str(e).splitlines()[-1]
            except IndexError:
                error = str(e)

            display.vvvvv(
                "{action}: {desc} fail {e_type} '{err}', retrying in {sleep:.4} seconds...\n{tcb}".format(
                    action=task_action,
                    desc=action_desc,
                    e_type=type(e).__name__,
                    err=error,
                    sleep=fail_sleep,
                    tcb=traceback.format_exc(),
                )
            )

            fail_count += 1
            time.sleep(fail_sleep)

    if last_error:
        raise last_error

    return None