def send_to_worker(cls, python, data):
        """Bounce a pickled object through another version of Python.
        This will send data to a child process where it will
        be unpickled, then repickled and sent back to the parent process.
        Args:
            python: list containing the python binary to start and its arguments
            data: bytes object to send to the child process
        Returns:
            The pickled data received from the child process.
        """
        worker = cls.worker
        if worker is None:
            worker = cls.start_worker(python)

        try:
            worker.stdin.write(struct.pack('!i', len(data)) + data)
            worker.stdin.flush()

            size, = struct.unpack('!i', read_exact(worker.stdout, 4))
            if size > 0:
                return read_exact(worker.stdout, size)
            # if the worker fails, it will write the exception to stdout
            if size < 0:
                stdout = read_exact(worker.stdout, -size)
                try:
                    exception = pickle.loads(stdout)
                except (pickle.UnpicklingError, EOFError):
                    pass
                else:
                    if isinstance(exception, Exception):
                        # To allow for tests which test for errors.
                        raise exception
            _, stderr = worker.communicate()
            raise RuntimeError(stderr)
        except:
            cls.finish_worker()
            raise