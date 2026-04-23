def test_subinterpreter_stack_trace(self):
        port = find_unused_port()

        import pickle

        subinterp_code = textwrap.dedent(f"""
            import socket
            import time

            def sub_worker():
                def nested_func():
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', {port}))
                    sock.sendall(b"ready:sub\\n")
                    time.sleep(10_000)
                nested_func()

            sub_worker()
        """).strip()

        pickled_code = pickle.dumps(subinterp_code)

        script = textwrap.dedent(
            f"""
            from concurrent import interpreters
            import time
            import sys
            import socket
            import threading

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', {port}))

            def main_worker():
                sock.sendall(b"ready:main\\n")
                time.sleep(10_000)

            def run_subinterp():
                subinterp = interpreters.create()
                import pickle
                pickled_code = {pickled_code!r}
                subinterp_code = pickle.loads(pickled_code)
                subinterp.exec(subinterp_code)

            sub_thread = threading.Thread(target=run_subinterp)
            sub_thread.start()

            main_thread = threading.Thread(target=main_worker)
            main_thread.start()

            main_thread.join()
            sub_thread.join()
            """
        )

        with os_helper.temp_dir() as work_dir:
            script_dir = os.path.join(work_dir, "script_pkg")
            os.mkdir(script_dir)

            server_socket = _create_server_socket(port)
            script_name = _make_test_script(script_dir, "script", script)
            client_sockets = []

            try:
                with _managed_subprocess([sys.executable, script_name]) as p:
                    # Accept connections from both main and subinterpreter
                    responses = set()
                    while len(responses) < 2:
                        try:
                            client_socket, _ = server_socket.accept()
                            client_sockets.append(client_socket)
                            response = client_socket.recv(1024)
                            if b"ready:main" in response:
                                responses.add("main")
                            if b"ready:sub" in response:
                                responses.add("sub")
                        except socket.timeout:
                            break

                    server_socket.close()
                    server_socket = None

                    stack_trace = get_stack_trace(p.pid)

                    # Verify we have at least one interpreter
                    self.assertGreaterEqual(len(stack_trace), 1)

                    # Look for main interpreter (ID 0) and subinterpreter (ID > 0)
                    main_interp = None
                    sub_interp = None
                    for interpreter_info in stack_trace:
                        if interpreter_info.interpreter_id == 0:
                            main_interp = interpreter_info
                        elif interpreter_info.interpreter_id > 0:
                            sub_interp = interpreter_info

                    self.assertIsNotNone(
                        main_interp, "Main interpreter should be present"
                    )

                    # Check main interpreter has expected stack trace
                    main_found = self._find_frame_in_trace(
                        [main_interp], lambda f: f.funcname == "main_worker"
                    )
                    self.assertIsNotNone(
                        main_found,
                        "Main interpreter should have main_worker in stack",
                    )

                    # If subinterpreter is present, check its stack trace
                    if sub_interp:
                        sub_found = self._find_frame_in_trace(
                            [sub_interp],
                            lambda f: f.funcname
                            in ("sub_worker", "nested_func"),
                        )
                        self.assertIsNotNone(
                            sub_found,
                            "Subinterpreter should have sub_worker or nested_func in stack",
                        )
            finally:
                _cleanup_sockets(*client_sockets, server_socket)