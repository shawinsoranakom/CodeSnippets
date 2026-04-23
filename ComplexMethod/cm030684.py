def do_test(
        self,
        *,
        incoming,
        simulate_send_failure=False,
        simulate_sigint_during_stdout_write=False,
        use_interrupt_socket=False,
        expected_outgoing=None,
        expected_outgoing_signals=None,
        expected_completions=None,
        expected_exception=None,
        expected_stdout="",
        expected_stdout_substring="",
        expected_state=None,
    ):
        if expected_outgoing is None:
            expected_outgoing = []
        if expected_outgoing_signals is None:
            expected_outgoing_signals = []
        if expected_completions is None:
            expected_completions = []
        if expected_state is None:
            expected_state = {}

        expected_state.setdefault("write_failed", False)
        messages = [m for source, m in incoming if source == "server"]
        prompts = [m["prompt"] for source, m in incoming if source == "user"]

        input_iter = (m for source, m in incoming if source == "user")
        completions = []

        def mock_input(prompt):
            message = next(input_iter, None)
            if message is None:
                raise EOFError

            if req := message.get("completion_request"):
                readline_mock = unittest.mock.Mock()
                readline_mock.get_line_buffer.return_value = req["line"]
                readline_mock.get_begidx.return_value = req["begidx"]
                readline_mock.get_endidx.return_value = req["endidx"]
                unittest.mock.seal(readline_mock)
                with unittest.mock.patch.dict(sys.modules, {"readline": readline_mock}):
                    for param in itertools.count():
                        prefix = req["line"][req["begidx"] : req["endidx"]]
                        completion = client.complete(prefix, param)
                        if completion is None:
                            break
                        completions.append(completion)

            reply = message["input"]
            if isinstance(reply, BaseException):
                raise reply
            if isinstance(reply, str):
                return reply
            return reply()

        with ExitStack() as stack:
            client_sock, server_sock = socket.socketpair()
            stack.enter_context(closing(client_sock))
            stack.enter_context(closing(server_sock))

            server_sock = unittest.mock.Mock(wraps=server_sock)

            client_sock.sendall(
                b"".join(
                    (m if isinstance(m, bytes) else json.dumps(m).encode()) + b"\n"
                    for m in messages
                )
            )
            client_sock.shutdown(socket.SHUT_WR)

            if simulate_send_failure:
                server_sock.sendall = unittest.mock.Mock(
                    side_effect=OSError("sendall failed")
                )
                client_sock.shutdown(socket.SHUT_RD)

            stdout = io.StringIO()

            if simulate_sigint_during_stdout_write:
                orig_stdout_write = stdout.write

                def sigint_stdout_write(s):
                    signal.raise_signal(signal.SIGINT)
                    return orig_stdout_write(s)

                stdout.write = sigint_stdout_write

            input_mock = stack.enter_context(
                unittest.mock.patch("pdb.input", side_effect=mock_input)
            )
            stack.enter_context(redirect_stdout(stdout))

            if use_interrupt_socket:
                interrupt_sock = unittest.mock.Mock(spec=socket.socket)
                mock_kill = None
            else:
                interrupt_sock = None
                mock_kill = stack.enter_context(
                    unittest.mock.patch("os.kill", spec=os.kill)
                )

            client = _PdbClient(
                pid=12345,
                server_socket=server_sock,
                interrupt_sock=interrupt_sock,
            )

            if expected_exception is not None:
                exception = expected_exception["exception"]
                msg = expected_exception["msg"]
                stack.enter_context(self.assertRaises(exception, msg=msg))

            client.cmdloop()

        sent_msgs = [msg.args[0] for msg in server_sock.sendall.mock_calls]
        for msg in sent_msgs:
            assert msg.endswith(b"\n")
        actual_outgoing = [json.loads(msg) for msg in sent_msgs]

        self.assertEqual(actual_outgoing, expected_outgoing)
        self.assertEqual(completions, expected_completions)
        if expected_stdout_substring and not expected_stdout:
            self.assertIn(expected_stdout_substring, stdout.getvalue())
        else:
            self.assertEqual(stdout.getvalue(), expected_stdout)
        input_mock.assert_has_calls([unittest.mock.call(p) for p in prompts])
        actual_state = {k: getattr(client, k) for k in expected_state}
        self.assertEqual(actual_state, expected_state)

        if use_interrupt_socket:
            outgoing_signals = [
                signal.Signals(int.from_bytes(call.args[0]))
                for call in interrupt_sock.sendall.call_args_list
            ]
        else:
            assert mock_kill is not None
            outgoing_signals = []
            for call in mock_kill.call_args_list:
                pid, signum = call.args
                self.assertEqual(pid, 12345)
                outgoing_signals.append(signal.Signals(signum))
        self.assertEqual(outgoing_signals, expected_outgoing_signals)