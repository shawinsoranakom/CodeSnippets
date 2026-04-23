def reboot_host(
    task_action: str,
    connection: ConnectionBase,
    boot_time_command: str = _DEFAULT_BOOT_TIME_COMMAND,
    connect_timeout: int = 5,
    msg: str = "Reboot initiated by Ansible",
    post_reboot_delay: int = 0,
    pre_reboot_delay: int = 2,
    reboot_timeout: int = 600,
    test_command: t.Optional[str] = None,
) -> t.Dict[str, t.Any]:
    """Reboot a Windows Host.

    Used by action plugins in ansible.windows to reboot a Windows host. It
    takes in the connection plugin so it can run the commands on the targeted
    host and monitor the reboot process. The return dict will have the
    following keys set:

        changed: Whether a change occurred (reboot was done)
        elapsed: Seconds elapsed between the reboot and it coming back online
        failed: Whether a failure occurred
        unreachable: Whether it failed to connect to the host on the first cmd
        rebooted: Whether the host was rebooted

    When failed=True there may be more keys to give some information around
    the failure like msg, exception. There are other keys that might be
    returned as well but they are dependent on the failure that occurred.

    Verbosity levels used:
        2: Message when each reboot step is completed
        4: Connection plugin operations and their results
        5: Raw commands run and the results of those commands
        Debug: Everything, very verbose

    Args:
        task_action: The name of the action plugin that is running for logging.
        connection: The connection plugin to run the reboot commands on.
        boot_time_command: The command to run when getting the boot timeout.
        connect_timeout: Override the connection timeout of the connection
            plugin when polling the rebooted host.
        msg: The message to display to interactive users when rebooting the
            host.
        post_reboot_delay: Seconds to wait after sending the reboot command
            before checking to see if it has returned.
        pre_reboot_delay: Seconds to wait when sending the reboot command.
        reboot_timeout: Seconds to wait while polling for the host to come
            back online.
        test_command: Command to run when the host is back online and
            determines the machine is ready for management. When not defined
            the default command should wait until the reboot is complete and
            all pre-login configuration has completed.

    Returns:
        (Dict[str, Any]): The return result as a dictionary. Use the 'failed'
            key to determine if there was a failure or not.
    """
    result: t.Dict[str, t.Any] = {
        "changed": False,
        "elapsed": 0,
        "failed": False,
        "unreachable": False,
        "rebooted": False,
    }
    host_context = {"do_close_on_reset": True}

    # Get current boot time. A lot of tasks that require a reboot leave the WSMan stack in a bad place. Will try to
    # get the initial boot time 3 times before giving up.
    try:
        previous_boot_time = _do_until_success_or_retry_limit(
            task_action,
            connection,
            host_context,
            "pre-reboot boot time check",
            3,
            _get_system_boot_time,
            task_action,
            connection,
            boot_time_command,
        )

    except Exception as e:
        # Report a the failure based on the last exception received.
        if isinstance(e, _ReturnResultException):
            result.update(e.result)

        if isinstance(e, AnsibleConnectionFailure):
            result["unreachable"] = True
        else:
            result["failed"] = True

        result["msg"] = str(e)
        result["exception"] = traceback.format_exc()
        return result

    # Get the original connection_timeout option var so it can be reset after
    original_connection_timeout: t.Optional[float] = None
    try:
        original_connection_timeout = connection.get_option("connection_timeout")
        display.vvvv(
            f"{task_action}: saving original connection_timeout of {original_connection_timeout}"
        )
    except KeyError:
        display.vvvv(
            f"{task_action}: connection_timeout connection option has not been set"
        )

    # Initiate reboot
    # This command may be wrapped in other shells or command making it hard to detect what shutdown.exe actually
    # returned. We use this hackery to return a json that contains the stdout/stderr/rc as a structured object for our
    # code to parse and detect if something went wrong.
    reboot_command = """$ErrorActionPreference = 'Continue'

if ($%s) {
    Remove-Item -LiteralPath '%s' -Force -ErrorAction SilentlyContinue
}

$stdout = $null
$stderr = . { shutdown.exe /r /t %s /c %s | Set-Variable stdout } 2>&1 | ForEach-Object ToString

ConvertTo-Json -Compress -InputObject @{
    stdout = (@($stdout) -join "`n")
    stderr = (@($stderr) -join "`n")
    rc = $LASTEXITCODE
}
""" % (
        str(not test_command),
        _LOGON_UI_KEY,
        int(pre_reboot_delay),
        quote_pwsh(msg),
    )

    expected_test_result = (
        None  # We cannot have an expected result if the command is user defined
    )
    if not test_command:
        # It turns out that LogonUI will create this registry key if it does not exist when it's about to show the
        # logon prompt. Normally this is a volatile key but if someone has explicitly created it that might no longer
        # be the case. We ensure it is not present on a reboot so we can wait until LogonUI creates it to determine
        # the host is actually online and ready, e.g. no configurations/updates still to be applied.
        # We echo a known successful statement to catch issues with powershell failing to start but the rc mysteriously
        # being 0 causing it to consider a successful reboot too early (seen on ssh connections).
        expected_test_result = f"success-{uuid.uuid4()}"
        test_command = f"Get-Item -LiteralPath '{_LOGON_UI_KEY}' -ErrorAction Stop; '{expected_test_result}'"

    start = None
    try:
        _perform_reboot(task_action, connection, reboot_command)

        start = datetime.datetime.utcnow()
        result["changed"] = True
        result["rebooted"] = True

        if post_reboot_delay != 0:
            display.vv(
                f"{task_action}: waiting an additional {post_reboot_delay} seconds"
            )
            time.sleep(post_reboot_delay)

        # Keep on trying to run the last boot time check until it is successful or the timeout is raised
        display.vv(f"{task_action} validating reboot")
        _do_until_success_or_timeout(
            task_action,
            connection,
            host_context,
            "last boot time check",
            reboot_timeout,
            _check_boot_time,
            task_action,
            connection,
            host_context,
            previous_boot_time,
            boot_time_command,
            connect_timeout,
        )

        # Reset the connection plugin connection timeout back to the original
        if original_connection_timeout is not None:
            _set_connection_timeout(
                task_action,
                connection,
                host_context,
                original_connection_timeout,
            )

        # Run test command until ti is successful or a timeout occurs
        display.vv(f"{task_action} running post reboot test command")
        _do_until_success_or_timeout(
            task_action,
            connection,
            host_context,
            "post-reboot test command",
            reboot_timeout,
            _run_test_command,
            task_action,
            connection,
            test_command,
            expected=expected_test_result,
        )

        display.vv(f"{task_action}: system successfully rebooted")

    except Exception as e:
        if isinstance(e, _ReturnResultException):
            result.update(e.result)

        result["failed"] = True
        result["msg"] = str(e)
        result["exception"] = traceback.format_exc()

    if start:
        elapsed = datetime.datetime.utcnow() - start
        result["elapsed"] = elapsed.seconds

    return result