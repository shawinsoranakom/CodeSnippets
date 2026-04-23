def _perform_reboot(
    task_action: str,
    connection: ConnectionBase,
    reboot_command: str,
    handle_abort: bool = True,
) -> None:
    """Runs the reboot command"""
    display.vv(f"{task_action}: rebooting server...")

    stdout = stderr = None
    try:
        rc, stdout, stderr = _execute_command(task_action, connection, reboot_command)

    except AnsibleConnectionFailure as e:
        # If the connection is closed too quickly due to the system being shutdown, carry on
        display.vvvv(f"{task_action}: AnsibleConnectionFailure caught and handled: {e}")
        rc = 0

    if stdout:
        try:
            reboot_result = json.loads(stdout)
        except getattr(json.decoder, "JSONDecodeError", ValueError):
            # While the reboot command should output json it may have failed for some other reason. We continue
            # reporting with that output instead
            pass
        else:
            stdout = reboot_result.get("stdout", stdout)
            stderr = reboot_result.get("stderr", stderr)
            rc = int(reboot_result.get("rc", rc))

    # Test for "A system shutdown has already been scheduled. (1190)" and handle it gracefully
    if handle_abort and (rc == 1190 or (rc != 0 and stderr and "(1190)" in stderr)):
        display.warning("A scheduled reboot was preempted by Ansible.")

        # Try to abort (this may fail if it was already aborted)
        rc, stdout, stderr = _execute_command(
            task_action, connection, "shutdown.exe /a"
        )
        display.vvvv(
            f"{task_action}: result from trying to abort existing shutdown - rc: {rc}, stdout: {stdout}, stderr: {stderr}"
        )

        return _perform_reboot(
            task_action, connection, reboot_command, handle_abort=False
        )

    if rc != 0:
        msg = f"{task_action}: Reboot command failed"
        raise _ReturnResultException(msg, rc=rc, stdout=stdout, stderr=stderr)