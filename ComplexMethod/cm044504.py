def _read_stdout(self) -> None:
        """ Read stdout from the subprocess. """
        logger.debug("Opening stdout reader")
        assert self._process is not None
        while True:
            try:
                buff = self._process.stdout
                assert buff is not None
                output: str = buff.readline()
            except ValueError as err:
                if str(err).lower().startswith("i/o operation on closed file"):
                    break
                raise

            if output == "" and self._process.poll() is not None:
                break

            if output and self._process_progress_stdout(output):
                continue

            if output.strip():
                self._process_training_stdout(output)
                print(output.rstrip())

        returncode = self._process.poll()
        assert returncode is not None
        self._first_loss_seen = False
        message = self._set_final_status(returncode)
        self._wrapper.terminate(message)
        logger.debug("Terminated stdout reader. returncode: %s", returncode)