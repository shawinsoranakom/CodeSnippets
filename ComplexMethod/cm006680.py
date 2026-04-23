async def _kill_zombie_mcp_processes(self, port: int) -> bool:
        """Kill zombie MCP Composer processes that may be stuck.

        On Windows, sometimes MCP Composer processes start but fail to bind to port.
        These processes become "zombies" that need to be killed before retry.

        Args:
            port: The port that should be used

        Returns:
            True if zombie processes were found and killed
        """
        try:
            os_type = platform.system()
            if os_type != "Windows":
                return False

            await logger.adebug(f"Looking for zombie MCP Composer processes on Windows for port {port}...")

            # First, try to find and kill any process using the port directly
            # Use full path to netstat on Windows to avoid PATH issues
            netstat_cmd = os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32", "netstat.exe")  # noqa: PTH118
            netstat_result = await asyncio.to_thread(
                subprocess.run,
                [netstat_cmd, "-ano"],
                capture_output=True,
                text=True,
                check=False,
            )

            killed_any = False
            if netstat_result.returncode == 0:
                # Parse netstat output to find PIDs using our port
                pids_on_port: list[int] = []
                for line in netstat_result.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            try:
                                pid = int(parts[-1])
                                # Only kill if not tracked by us
                                if pid not in self._pid_to_project:
                                    pids_on_port.append(pid)
                                else:
                                    project = self._pid_to_project[pid]
                                    await logger.adebug(
                                        f"Process {pid} on port {port} is tracked, skipping (project: {project})"
                                    )
                            except (ValueError, IndexError):
                                continue

                if pids_on_port:
                    await logger.adebug(
                        f"Found {len(pids_on_port)} untracked process(es) on port {port}: {pids_on_port}"
                    )
                    for pid in pids_on_port:
                        try:
                            await logger.adebug(f"Killing process {pid} on port {port}...")
                            # Use full path to taskkill on Windows to avoid PATH issues
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
                                killed_any = True
                            else:
                                stderr_output = (
                                    kill_result.stderr.decode()
                                    if isinstance(kill_result.stderr, bytes)
                                    else kill_result.stderr
                                )
                                await logger.awarning(f"Failed to kill process {pid} on port {port}: {stderr_output}")
                        except Exception as e:  # noqa: BLE001
                            await logger.adebug(f"Error killing process {pid}: {e}")

            # Also look for any orphaned mcp-composer processes (without checking port)
            # This catches processes that failed to bind but are still running
            # Use PowerShell instead of deprecated wmic.exe for Windows 10/11 compatibility
            try:
                # Use PowerShell to get Python processes with command line info
                # Build PowerShell command to find MCP Composer processes
                ps_filter = (
                    f"$_.Name -eq 'python.exe' -and $_.CommandLine -like '*mcp-composer*' "
                    f"-and ($_.CommandLine -like '*--port {port}*' -or $_.CommandLine -like '*--port={port}*')"
                )
                ps_cmd = (
                    f"Get-WmiObject Win32_Process | Where-Object {{ {ps_filter} }} | "
                    "Select-Object ProcessId,CommandLine | ConvertTo-Json"
                )
                powershell_cmd = ["powershell.exe", "-NoProfile", "-Command", ps_cmd]

                ps_result = await asyncio.to_thread(
                    subprocess.run,
                    powershell_cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                )

                if ps_result.returncode == 0 and ps_result.stdout.strip():
                    try:
                        # PowerShell may return single object or array
                        processes = json.loads(ps_result.stdout)
                        if isinstance(processes, dict):
                            processes = [processes]
                        elif not isinstance(processes, list):
                            processes = []

                        for proc in processes:
                            try:
                                pid = int(proc.get("ProcessId", 0))
                                if pid <= 0 or pid in self._pid_to_project:
                                    continue

                                await logger.adebug(
                                    f"Found orphaned MCP Composer process {pid} for port {port}, killing it"
                                )
                                # Use full path to taskkill on Windows to avoid PATH issues
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
                                    await logger.adebug(f"Successfully killed orphaned process {pid}")
                                    killed_any = True

                            except (ValueError, KeyError) as e:
                                await logger.adebug(f"Error processing PowerShell result: {e}")
                                continue

                    except json.JSONDecodeError as e:
                        await logger.adebug(f"Failed to parse PowerShell output: {e}")

            except asyncio.TimeoutError:
                await logger.adebug("PowerShell command timed out while checking for orphaned processes")
            except Exception as e:  # noqa: BLE001
                await logger.adebug(f"Error using PowerShell to find orphaned processes: {e}")

            if killed_any:
                # Give Windows time to clean up
                await logger.adebug("Waiting 3 seconds for Windows to release port...")
                await asyncio.sleep(3)

            return killed_any  # noqa: TRY300

        except Exception as e:  # noqa: BLE001
            await logger.adebug(f"Error killing zombie processes: {e}")
            return False