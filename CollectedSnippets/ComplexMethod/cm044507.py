def _compile_display_data(self) -> bool:
        """ Compile the data to be displayed.

        Returns
        -------
        bool
            ``True`` if there is valid data to display, ``False`` if not
        """
        if self._thread is None:
            logger.debug("Compiling Display Data in background thread")
            loss_keys = [key for key, val in self._vars.loss_keys.items()
                         if val.get()]
            logger.debug("Selected loss_keys: %s", loss_keys)

            selections = self._selections_to_list()

            if not self._check_valid_selection(loss_keys, selections):
                logger.warning("No data to display. Not refreshing")
                return False
            self._vars.status.set("Loading Data...")

            if self._graph is not None:
                self._graph.pack_forget()
            self._lbl_loading.pack(fill=tk.BOTH, expand=True)
            self.update_idletasks()

            kwargs = {"session_id": self._session_id,
                      "display": self._vars.display.get(),
                      "loss_keys": loss_keys,
                      "selections": selections,
                      "avg_samples": self._vars.avgiterations.get(),
                      "smooth_amount": self._vars.smoothamount.get(),
                      "flatten_outliers": self._vars.outliers.get()}
            self._thread = LongRunningTask(target=self._get_display_data,
                                           kwargs=kwargs,
                                           widget=self)
            self._thread.start()
            self.after(1000, self._compile_display_data)
            return True
        if not self._thread.complete.is_set():
            logger.debug("Popup Data not yet available")
            self.after(1000, self._compile_display_data)
            return True

        logger.debug("Getting Popup from background Thread")
        self._display_data = self._thread.get_result()
        self._thread = None
        if not self._check_valid_data():
            logger.warning("No valid data to display. Not refreshing")
            self._vars.status.set("")
            return False
        logger.debug("Compiled Display Data")
        self._vars.buildgraph.set(True)
        return True