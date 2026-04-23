def test_multiple_subinterpreters_with_threads(self):
        port = find_unused_port()

        import pickle

        subinterp1_code = textwrap.dedent(f"""
            import socket
            import time
            import threading

            def worker1():
                def nested_func():
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', {port}))
                    sock.sendall(b"ready:sub1-t1\\n")
                    time.sleep(10_000)
                nested_func()

            def worker2():
                def nested_func():
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', {port}))
                    sock.sendall(b"ready:sub1-t2\\n")
                    time.sleep(10_000)
                nested_func()

            t1 = threading.Thread(target=worker1)
            t2 = threading.Thread(target=worker2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
        """).strip()

        subinterp2_code = textwrap.dedent(f"""
            import socket
            import time
            import threading

            def worker1():
                def nested_func():
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', {port}))
                    sock.sendall(b"ready:sub2-t1\\n")
                    time.sleep(10_000)
                nested_func()

            def worker2():
                def nested_func():
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', {port}))
                    sock.sendall(b"ready:sub2-t2\\n")
                    time.sleep(10_000)
                nested_func()

            t1 = threading.Thread(target=worker1)
            t2 = threading.Thread(target=worker2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
        """).strip()

        pickled_code1 = pickle.dumps(subinterp1_code)
        pickled_code2 = pickle.dumps(subinterp2_code)

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

            def run_subinterp1():
                subinterp = interpreters.create()
                import pickle
                pickled_code = {pickled_code1!r}
                subinterp_code = pickle.loads(pickled_code)
                subinterp.exec(subinterp_code)

            def run_subinterp2():
                subinterp = interpreters.create()
                import pickle
                pickled_code = {pickled_code2!r}
                subinterp_code = pickle.loads(pickled_code)
                subinterp.exec(subinterp_code)

            sub1_thread = threading.Thread(target=run_subinterp1)
            sub2_thread = threading.Thread(target=run_subinterp2)
            sub1_thread.start()
            sub2_thread.start()

            main_thread = threading.Thread(target=main_worker)
            main_thread.start()

            main_thread.join()
            sub1_thread.join()
            sub2_thread.join()
            """
        )

        with os_helper.temp_dir() as work_dir:
            script_dir = os.path.join(work_dir, "script_pkg")
            os.mkdir(script_dir)

            server_socket = _create_server_socket(port, backlog=5)
            script_name = _make_test_script(script_dir, "script", script)
            client_sockets = []

            try:
                with _managed_subprocess([sys.executable, script_name]) as p:
                    # Accept connections from main and all subinterpreter threads
                    expected_responses = {
                        "ready:main",
                        "ready:sub1-t1",
                        "ready:sub1-t2",
                        "ready:sub2-t1",
                        "ready:sub2-t2",
                    }
                    responses = set()

                    while len(responses) < 5:
                        try:
                            client_socket, _ = server_socket.accept()
                            client_sockets.append(client_socket)
                            response = client_socket.recv(1024)
                            response_str = response.decode().strip()
                            if response_str in expected_responses:
                                responses.add(response_str)
                        except socket.timeout:
                            break

                    server_socket.close()
                    server_socket = None

                    stack_trace = get_stack_trace(p.pid)

                    # Verify we have multiple interpreters
                    self.assertGreaterEqual(len(stack_trace), 2)

                    # Count interpreters by ID
                    interpreter_ids = {
                        interp.interpreter_id for interp in stack_trace
                    }
                    self.assertIn(
                        0,
                        interpreter_ids,
                        "Main interpreter should be present",
                    )
                    self.assertGreaterEqual(len(interpreter_ids), 3)

                    # Count total threads
                    total_threads = sum(
                        len(interp.threads) for interp in stack_trace
                    )
                    self.assertGreaterEqual(total_threads, 5)

                    # Look for expected function names
                    all_funcnames = set()
                    for interpreter_info in stack_trace:
                        for thread_info in interpreter_info.threads:
                            for frame in thread_info.frame_info:
                                all_funcnames.add(frame.funcname)

                    expected_funcs = {
                        "main_worker",
                        "worker1",
                        "worker2",
                        "nested_func",
                    }
                    found_funcs = expected_funcs.intersection(all_funcnames)
                    self.assertGreater(len(found_funcs), 0)
            finally:
                _cleanup_sockets(*client_sockets, server_socket)