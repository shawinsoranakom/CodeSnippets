def _run_thread_status_test(self, mode, check_condition):
        """
        Common pattern for thread status detection tests.

        Args:
            mode: Profiling mode (PROFILING_MODE_CPU, PROFILING_MODE_GIL, etc.)
            check_condition: Function(statuses, sleeper_tid, busy_tid) -> bool
        """
        port = find_unused_port()
        script = textwrap.dedent(
            f"""\
            import time, sys, socket, threading
            import os

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', {port}))

            def sleeper():
                tid = threading.get_native_id()
                sock.sendall(f'ready:sleeper:{{tid}}\\n'.encode())
                time.sleep(10000)

            def busy():
                tid = threading.get_native_id()
                sock.sendall(f'ready:busy:{{tid}}\\n'.encode())
                x = 0
                while True:
                    x = x + 1
                time.sleep(0.5)

            t1 = threading.Thread(target=sleeper)
            t2 = threading.Thread(target=busy)
            t1.start()
            t2.start()
            sock.sendall(b'ready:main\\n')
            t1.join()
            t2.join()
            sock.close()
            """
        )

        with os_helper.temp_dir() as work_dir:
            script_dir = os.path.join(work_dir, "script_pkg")
            os.mkdir(script_dir)

            server_socket = _create_server_socket(port)
            script_name = _make_test_script(
                script_dir, "thread_status_script", script
            )
            client_socket = None

            try:
                with _managed_subprocess([sys.executable, script_name]) as p:
                    client_socket, _ = server_socket.accept()
                    server_socket.close()
                    server_socket = None

                    # Wait for all ready signals and parse TIDs
                    response = _wait_for_signal(
                        client_socket,
                        [b"ready:main", b"ready:sleeper", b"ready:busy"],
                    )

                    sleeper_tid = None
                    busy_tid = None
                    for line in response.split(b"\n"):
                        if line.startswith(b"ready:sleeper:"):
                            try:
                                sleeper_tid = int(line.split(b":")[-1])
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith(b"ready:busy:"):
                            try:
                                busy_tid = int(line.split(b":")[-1])
                            except (ValueError, IndexError):
                                pass

                    self.assertIsNotNone(
                        sleeper_tid, "Sleeper thread id not received"
                    )
                    self.assertIsNotNone(
                        busy_tid, "Busy thread id not received"
                    )

                    # Sample until we see expected thread states
                    statuses = {}
                    unwinder = RemoteUnwinder(
                        p.pid,
                        all_threads=True,
                        mode=mode,
                        skip_non_matching_threads=False,
                    )
                    for _ in busy_retry(SHORT_TIMEOUT):
                        with contextlib.suppress(*TRANSIENT_ERRORS):
                            traces = unwinder.get_stack_trace()
                            statuses = self._get_thread_statuses(traces)

                            if check_condition(
                                statuses, sleeper_tid, busy_tid
                            ):
                                break

                    return statuses, sleeper_tid, busy_tid
            finally:
                _cleanup_sockets(client_socket, server_socket)