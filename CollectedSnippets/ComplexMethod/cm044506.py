def _capture_loss(self, string: str) -> bool:
        """ Capture loss values from stdout

        Parameters
        ----------
        string: str
            An output line read from stdout

        Returns
        -------
        bool
            ``True`` if a loss line was captured from stdout, otherwise ``False``
        """
        logger.trace("Capturing loss")  # type:ignore[attr-defined]
        if not str.startswith(string, "["):
            logger.trace("Not loss message. Returning False")  # type:ignore[attr-defined]
            return False

        loss = self._consoleregex["loss"].findall(string)
        if len(loss) != 2 or not all(len(itm) == 3 for itm in loss):
            logger.trace("Not loss message. Returning False")  # type:ignore[attr-defined]
            return False

        message = f"Total Iterations: {int(loss[0][0])} | "
        message += "  ".join([f"{itm[1]}: {itm[2]}" for itm in loss])
        if not message:
            logger.trace(  # type:ignore[attr-defined]
                "Error creating loss message. Returning False")
            return False

        iterations = self._train_stats["iterations"]
        assert isinstance(iterations, int)

        if iterations == 0:
            # Set initial timestamp
            self._train_stats["timestamp"] = time()

        iterations += 1
        self._train_stats["iterations"] = iterations

        elapsed = self._calculate_elapsed()
        message = (f"Elapsed: {elapsed} | "
                   f"Session Iterations: {self._train_stats['iterations']}  {message}")

        if not self._first_loss_seen:
            self._statusbar.set_mode("indeterminate")
            self._first_loss_seen = True

        self._statusbar.progress_update(message, 0, False)
        logger.trace("Succesfully captured loss: %s", message)  # type:ignore[attr-defined]
        return True