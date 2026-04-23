def run(self):
        try:
            log_messages = self.connection.get_option('persistent_log_messages')
            while not self.connection._conn_closed:
                signal.signal(signal.SIGALRM, self.connect_timeout)
                signal.signal(signal.SIGTERM, self.handler)
                signal.alarm(self.connection.get_option('persistent_connect_timeout'))

                self.exception = None
                (s, addr) = self.sock.accept()
                signal.alarm(0)
                signal.signal(signal.SIGALRM, self.command_timeout)
                while True:
                    data = recv_data(s)
                    if not data:
                        break

                    if log_messages:
                        display.display("jsonrpc request: %s" % data, log_only=True)

                    request = json.loads(to_text(data, errors='surrogate_or_strict'))
                    if request.get('method') == "exec_command" and not self.connection.connected:
                        self.connection._connect()

                    signal.alarm(self.connection.get_option('persistent_command_timeout'))

                    resp = self.srv.handle_request(data)
                    signal.alarm(0)

                    if log_messages:
                        display.display("jsonrpc response: %s" % resp, log_only=True)

                    send_data(s, to_bytes(resp))

                s.close()

        except Exception as e:
            # socket.accept() will raise EINTR if the socket.close() is called
            if hasattr(e, 'errno'):
                if e.errno != errno.EINTR:
                    self.exception = traceback.format_exc()
            else:
                self.exception = traceback.format_exc()

        finally:
            # allow time for any exception msg send over socket to receive at other end before shutting down
            time.sleep(0.1)

            # when done, close the connection properly and cleanup the socket file so it can be recreated
            self.shutdown()