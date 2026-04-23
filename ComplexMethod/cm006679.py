async def _kill_process_on_port(self, port: int) -> bool:
        """Kill the process using the specified port.

        Cross-platform implementation supporting Windows, macOS, and Linux.

        Args:
            port: The port number to check

        Returns:
            True if a process was found and killed, False otherwise
        """
        try:
            await logger.adebug(f"Checking for processes using port {port}...")
            os_type = platform.system()

            # Platform-specific command to find PID
            if os_type == "Windows":
                # Use netstat on Windows - use full path to avoid PATH issues
                netstat_cmd = os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32", "netstat.exe")  # noqa: PTH118
                result = await asyncio.to_thread(
                    subprocess.run,
                    [netstat_cmd, "-ano"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode == 0:
                    # Parse netstat output to find PID
                    # Format: TCP    0.0.0.0:PORT    0.0.0.0:0    LISTENING    PID
                    windows_pids: list[int] = []
                    for line in result.stdout.split("\n"):
                        if f":{port}" in line and "LISTENING" in line:
                            parts = line.split()
                            if parts:
                                try:
                                    pid = int(parts[-1])
                                    windows_pids.append(pid)
                                except (ValueError, IndexError):
                                    continue

                    await logger.adebug(f"Found {len(windows_pids)} process(es) using port {port}: {windows_pids}")

                    for pid in windows_pids:
                        try:
                            await logger.adebug(f"Attempting to kill process {pid} on port {port}...")
                            # Use taskkill on Windows - use full path to avoid PATH issues
                            taskkill_cmd = os.path.join(  # noqa: PTH118
                                os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32", "taskkill.exe"
                            )
                            kill_result = await asyncio.to_thread(
                                subprocess.run,
                                [taskkill_cmd, "/F", "/PID", str(pid)],
                                capture_output=True,
                                check=False,
                            )

                            if kill_result.returncode == 0:
                                await logger.adebug(f"Successfully killed process {pid} on port {port}")
                                return True
                            await logger.awarning(
                                f"taskkill returned {kill_result.returncode} for process {pid} on port {port}"
                            )
                        except Exception as e:  # noqa: BLE001
                            await logger.aerror(f"Error killing PID {pid}: {e}")

                    return False
            else:
                # Use lsof on Unix-like systems (macOS, Linux)
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                await logger.adebug(f"lsof returned code {result.returncode} for port {port}")

                # Extract PIDs from lsof output
                lsof_output = result.stdout.strip()
                lsof_errors = result.stderr.strip()

                if lsof_output:
                    await logger.adebug(f"lsof stdout: {lsof_output}")
                if lsof_errors:
                    await logger.adebug(f"lsof stderr: {lsof_errors}")

                if result.returncode == 0 and lsof_output:
                    unix_pids = lsof_output.split("\n")
                    await logger.adebug(f"Found {len(unix_pids)} process(es) using port {port}: {unix_pids}")

                    for pid_str in unix_pids:
                        try:
                            pid = int(pid_str.strip())
                            await logger.adebug(f"Attempting to kill process {pid} on port {port}...")

                            # Try to kill the process
                            kill_result = await asyncio.to_thread(
                                subprocess.run,
                                ["kill", "-9", str(pid)],
                                capture_output=True,
                                check=False,
                            )

                            if kill_result.returncode == 0:
                                await logger.adebug(f"Successfully sent kill signal to process {pid} on port {port}")
                                return True
                            await logger.awarning(
                                f"kill command returned {kill_result.returncode} for process {pid} on port {port}"
                            )
                        except (ValueError, ProcessLookupError) as e:
                            await logger.aerror(f"Error processing PID {pid_str}: {e}")

                    # If we get here, we found processes but couldn't kill any
                    return False
                await logger.adebug(f"No process found using port {port}")
                return False
        except Exception as e:  # noqa: BLE001
            await logger.aerror(f"Error finding/killing process on port {port}: {e}")
            return False
        return False