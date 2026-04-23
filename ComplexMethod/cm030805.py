def test_thread_status_all_mode_detection(self):
        port = find_unused_port()
        script = textwrap.dedent(
            f"""\
            import socket
            import threading
            import time
            import sys

            def sleeper_thread():
                conn = socket.create_connection(("localhost", {port}))
                conn.sendall(b"sleeper:" + str(threading.get_native_id()).encode())
                while True:
                    time.sleep(1)

            def busy_thread():
                conn = socket.create_connection(("localhost", {port}))
                conn.sendall(b"busy:" + str(threading.get_native_id()).encode())
                while True:
                    sum(range(100000))

            t1 = threading.Thread(target=sleeper_thread)
            t2 = threading.Thread(target=busy_thread)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            """
        )

        with os_helper.temp_dir() as tmp_dir:
            script_file = make_script(tmp_dir, "script", script)
            server_socket = _create_server_socket(port, backlog=2)
            client_sockets = []

            try:
                with _managed_subprocess(
                    [sys.executable, script_file],
                ) as p:
                    sleeper_tid = None
                    busy_tid = None

                    # Receive thread IDs from the child process
                    for _ in range(2):
                        client_socket, _ = server_socket.accept()
                        client_sockets.append(client_socket)
                        line = client_socket.recv(1024)
                        if line:
                            if line.startswith(b"sleeper:"):
                                try:
                                    sleeper_tid = int(line.split(b":")[-1])
                                except (ValueError, IndexError):
                                    pass
                            elif line.startswith(b"busy:"):
                                try:
                                    busy_tid = int(line.split(b":")[-1])
                                except (ValueError, IndexError):
                                    pass

                    server_socket.close()
                    server_socket = None

                    statuses = {}
                    unwinder = RemoteUnwinder(
                        p.pid,
                        all_threads=True,
                        mode=PROFILING_MODE_ALL,
                        skip_non_matching_threads=False,
                    )
                    for _ in busy_retry(SHORT_TIMEOUT):
                        with contextlib.suppress(*TRANSIENT_ERRORS):
                            traces = unwinder.get_stack_trace()
                            statuses = self._get_thread_statuses(traces)

                            # Check ALL mode provides both GIL and CPU info
                            if (
                                sleeper_tid in statuses
                                and busy_tid in statuses
                                and not (
                                    statuses[sleeper_tid]
                                    & THREAD_STATUS_ON_CPU
                                )
                                and not (
                                    statuses[sleeper_tid]
                                    & THREAD_STATUS_HAS_GIL
                                )
                                and (statuses[busy_tid] & THREAD_STATUS_ON_CPU)
                                and (
                                    statuses[busy_tid] & THREAD_STATUS_HAS_GIL
                                )
                            ):
                                break

                    self.assertIsNotNone(
                        sleeper_tid, "Sleeper thread id not received"
                    )
                    self.assertIsNotNone(
                        busy_tid, "Busy thread id not received"
                    )
                    self.assertIn(sleeper_tid, statuses)
                    self.assertIn(busy_tid, statuses)

                    # Sleeper: off CPU, no GIL
                    self.assertFalse(
                        statuses[sleeper_tid] & THREAD_STATUS_ON_CPU,
                        "Sleeper should be off CPU",
                    )
                    self.assertFalse(
                        statuses[sleeper_tid] & THREAD_STATUS_HAS_GIL,
                        "Sleeper should not have GIL",
                    )

                    # Busy: on CPU, has GIL
                    self.assertTrue(
                        statuses[busy_tid] & THREAD_STATUS_ON_CPU,
                        "Busy should be on CPU",
                    )
                    self.assertTrue(
                        statuses[busy_tid] & THREAD_STATUS_HAS_GIL,
                        "Busy should have GIL",
                    )
            finally:
                _cleanup_sockets(*client_sockets, server_socket)