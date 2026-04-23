def test_only_active_thread(self):
        port = find_unused_port()
        script = textwrap.dedent(
            f"""\
            import time, sys, socket, threading

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', {port}))

            def worker_thread(name, barrier, ready_event):
                barrier.wait()
                ready_event.wait()
                time.sleep(10_000)

            def main_work():
                sock.sendall(b"working\\n")
                count = 0
                while count < 100000000:
                    count += 1
                    if count % 10000000 == 0:
                        pass
                sock.sendall(b"done\\n")

            num_threads = 3
            barrier = threading.Barrier(num_threads + 1)
            ready_event = threading.Event()

            threads = []
            for i in range(num_threads):
                t = threading.Thread(target=worker_thread, args=(f"Worker-{{i}}", barrier, ready_event))
                t.start()
                threads.append(t)

            barrier.wait()
            sock.sendall(b"ready\\n")
            ready_event.set()
            main_work()
            """
        )

        with os_helper.temp_dir() as work_dir:
            script_dir = os.path.join(work_dir, "script_pkg")
            os.mkdir(script_dir)

            server_socket = _create_server_socket(port)
            script_name = _make_test_script(script_dir, "script", script)
            client_socket = None

            try:
                with _managed_subprocess([sys.executable, script_name]) as p:
                    client_socket, _ = server_socket.accept()
                    server_socket.close()
                    server_socket = None

                    # Wait for ready and working signals
                    _wait_for_signal(client_socket, [b"ready", b"working"])

                    # Get stack trace with all threads
                    unwinder_all = RemoteUnwinder(p.pid, all_threads=True)
                    for _ in busy_retry(SHORT_TIMEOUT):
                        with contextlib.suppress(*TRANSIENT_ERRORS):
                            all_traces = unwinder_all.get_stack_trace()
                            found = self._find_frame_in_trace(
                                all_traces,
                                lambda f: f.funcname == "main_work"
                                and f.location.lineno > 12,
                            )
                            if found:
                                break
                    else:
                        self.fail(
                            "Main thread did not start its busy work on time"
                        )

                    # Get stack trace with only GIL holder
                    unwinder_gil = RemoteUnwinder(
                        p.pid, only_active_thread=True
                    )
                    # Use condition to retry until we capture a thread holding the GIL
                    # (sampling may catch moments with no GIL holder on slow CI)
                    gil_traces = _get_stack_trace_with_retry(
                        unwinder_gil,
                        condition=lambda t: sum(len(i.threads) for i in t) >= 1,
                    )

                    # Count threads
                    total_threads = sum(
                        len(interp.threads) for interp in all_traces
                    )
                    self.assertGreater(total_threads, 1)

                    total_gil_threads = sum(
                        len(interp.threads) for interp in gil_traces
                    )
                    self.assertEqual(total_gil_threads, 1)

                    # Get the GIL holder thread ID
                    gil_thread_id = None
                    for interpreter_info in gil_traces:
                        if interpreter_info.threads:
                            gil_thread_id = interpreter_info.threads[
                                0
                            ].thread_id
                            break

                    # Get all thread IDs
                    all_thread_ids = []
                    for interpreter_info in all_traces:
                        for thread_info in interpreter_info.threads:
                            all_thread_ids.append(thread_info.thread_id)

                    self.assertIn(gil_thread_id, all_thread_ids)
            finally:
                _cleanup_sockets(client_socket, server_socket)