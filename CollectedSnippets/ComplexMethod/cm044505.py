def _read_stderr(self) -> None:
        """ Read stdout from the subprocess. If training, pass the loss
        values to Queue """
        logger.debug("Opening stderr reader")
        assert self._process is not None
        while True:
            try:
                buff = self._process.stderr
                assert buff is not None
                output: str = buff.readline()
            except ValueError as err:
                if str(err).lower().startswith("i/o operation on closed file"):
                    break
                raise
            if output == "" and self._process.poll() is not None:
                break
            if output:
                if self._command != "train" and self._capture_tqdm(output):
                    continue
                if self._process_training_determinate_function(output):
                    continue
                print(output.strip(), file=sys.stderr)
        logger.debug("Terminated stderr reader")