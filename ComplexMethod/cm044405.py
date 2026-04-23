def _monitor(self, thread: MultiThread) -> bool:
        """Monitor the background :func:`_training` thread for key presses and errors.

        Parameters
        ----------
        thread
            The thread containing the training loop

        Returns
        -------
        ``True`` if there has been an error in the background thread otherwise ``False``
        """
        self._output_startup_info()
        keypress = KBHit(is_gui=self._args.redirect_gui)
        err = False
        while True:
            try:
                if thread.has_error:
                    logger.debug("[Train] Thread error detected")
                    err = True
                    break
                if self._stop:
                    logger.debug("[Train] Stop received")
                    break

                # Preview Monitor
                if self._preview.should_quit:
                    break
                if self._preview.should_save:
                    self._save_now = True

                # Console Monitor
                if self._check_keypress(keypress):
                    break  # Exit requested

                sleep(1)
            except KeyboardInterrupt:
                logger.debug("[Train] Keyboard Interrupt received")
                break
        logger.debug("[Train] Closing Monitor")
        self._preview.shutdown()
        keypress.set_normal_term()
        logger.debug("[Train] Closed Monitor")
        return err