def _process_progress_stdout(self, output: str) -> bool:
        """ Process stdout for any faceswap processes that update the status/progress bar(s)

        Parameters
        ----------
        output: str
            The output line read from stdout

        Returns
        -------
        bool
            ``True`` if all actions have been completed on the output line otherwise ``False``
        """
        if self._process_training_determinate_function(output):
            return True

        if self._command == "train" and self._capture_loss(output):
            return True

        if self._command == "train" and output.strip() == "\x1b[2K":  # Clear line command for cli
            return True

        if self._command == "effmpeg" and self._capture_ffmpeg(output):
            return True

        if self._command not in ("train", "effmpeg") and self._capture_tqdm(output):
            return True

        return False