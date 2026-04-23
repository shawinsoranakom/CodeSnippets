def start_container(
        self,
        container_name_or_id: str,
        stdin=None,
        interactive: bool = False,
        attach: bool = False,
        flags: str | None = None,
    ) -> tuple[bytes, bytes]:
        LOG.debug("Starting container %s", container_name_or_id)
        try:
            container = self.client().containers.get(container_name_or_id)
            stdout = to_bytes(container_name_or_id)
            stderr = b""
            if interactive or attach:
                params = {"stdout": 1, "stderr": 1, "stream": 1}
                if interactive:
                    params["stdin"] = 1
                sock = container.attach_socket(params=params)
                sock = sock._sock if hasattr(sock, "_sock") else sock
                result_queue = queue.Queue()
                thread_started = threading.Event()
                start_waiting = threading.Event()

                # Note: We need to be careful about potential race conditions here - .wait() should happen right
                #   after .start(). Hence starting a thread and asynchronously waiting for the container exit code
                def wait_for_result(*_):
                    _exit_code = -1
                    try:
                        thread_started.set()
                        start_waiting.wait()
                        _exit_code = container.wait()["StatusCode"]
                    except APIError as e:
                        _exit_code = 1
                        raise ContainerException(str(e))
                    finally:
                        result_queue.put(_exit_code)

                # start listener thread
                start_worker_thread(wait_for_result)
                thread_started.wait()
                try:
                    # start container
                    container.start()
                finally:
                    # start awaiting container result
                    start_waiting.set()

                # handle container input/output
                # under windows, the socket has no __enter__ / cannot be used as context manager
                # therefore try/finally instead of with here
                try:
                    if stdin:
                        sock.sendall(to_bytes(stdin))
                        sock.shutdown(socket.SHUT_WR)
                    stdout, stderr = self._read_from_sock(sock, False)
                except TimeoutError:
                    LOG.debug(
                        "Socket timeout when talking to the I/O streams of Docker container '%s'",
                        container_name_or_id,
                    )
                finally:
                    sock.close()

                # get container exit code
                exit_code = result_queue.get()
                if exit_code:
                    raise ContainerException(
                        f"Docker container returned with exit code {exit_code}",
                        stdout=stdout,
                        stderr=stderr,
                    )
            else:
                container.start()
            return stdout, stderr
        except NotFound:
            raise NoSuchContainer(container_name_or_id)
        except APIError as e:
            raise ContainerException() from e