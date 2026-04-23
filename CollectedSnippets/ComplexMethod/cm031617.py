async def find_pid(serial):
    print("Waiting for app to start - this may take several minutes")
    shown_error = False
    while True:
        try:
            # `pidof` requires API level 24 or higher. The level 23 emulator
            # includes it, but it doesn't work (it returns all processes).
            pid = (await async_check_output(
                adb, "-s", serial, "shell", "pidof", "-s", APP_ID
            )).strip()
        except CalledProcessError as e:
            # If the app isn't running yet, pidof gives no output. So if there
            # is output, there must have been some other error. However, this
            # sometimes happens transiently, especially when running a managed
            # emulator for the first time, so don't make it fatal.
            if (e.stdout or e.stderr) and not shown_error:
                print_called_process_error(e)
                print("This may be transient, so continuing to wait")
                shown_error = True
        else:
            # Some older devices (e.g. Nexus 4) return zero even when no process
            # was found, so check whether we actually got any output.
            if pid:
                print(f"PID: {pid}")
                return pid

        # Loop fairly rapidly to avoid missing a short-lived process.
        await asyncio.sleep(0.2)