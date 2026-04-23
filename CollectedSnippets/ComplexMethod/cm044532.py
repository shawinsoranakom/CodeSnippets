def _get_raw(self) -> None:
        """ Obtain the raw loss values and add them to a new :attr:`stats` dictionary. """
        logger.debug("Getting Raw Data")
        self.stats.clear()
        iterations = set()

        if self._display.lower() == "loss":
            loss_dict = _SESSION.get_loss(self._session_id)
            for loss_name, loss in loss_dict.items():
                if loss_name not in self._loss_keys:
                    continue
                iterations.add(loss.shape[0])

                if self._limit > 0:
                    loss = loss[-self._limit:]

                if self._args["flatten_outliers"]:
                    loss = self._flatten_outliers(loss)

                self.stats[f"raw_{loss_name}"] = loss

            self._iterations = 0 if not iterations else min(iterations)
            if self._limit > 1:
                self._start_iteration = max(0, self._iterations - self._limit)
                self._iterations = min(self._iterations, self._limit)
            else:
                self._start_iteration = 0

            if len(iterations) > 1:
                # Crop all losses to the same number of items
                if self._iterations == 0:
                    self._stats = {lossname: np.array([], dtype=loss.dtype)
                                   for lossname, loss in self.stats.items()}
                else:
                    self._stats = {lossname: loss[:self._iterations]
                                   for lossname, loss in self.stats.items()}

        else:  # Rate calculation
            data = self._calc_rate_total() if self._is_totals else self._calc_rate()
            if self._args["flatten_outliers"]:
                data = self._flatten_outliers(data)
            self._iterations = data.shape[0]
            self.stats["raw_rate"] = data

        logger.debug("Got Raw Data: %s", {k: f"Total: {len(v)}, Min: {np.nanmin(v)}, "
                                             f"Max: {np.nanmax(v)}, "
                                             f"nans: {np.count_nonzero(np.isnan(v))}"
                                          for k, v in self.stats.items()})