def _get_calculations(self) -> None:
        """ Perform the required calculations and populate :attr:`stats`. """
        for selection in self._selections:
            if selection == "raw":
                continue
            logger.debug("Calculating: %s", selection)
            method = getattr(self, f"_calc_{selection}")
            raw_keys = [key for key in self._stats if key.startswith("raw_")]
            for key in raw_keys:
                selected_key = f"{selection}_{key.replace('raw_', '')}"
                self._stats[selected_key] = method(self._stats[key])
        logger.debug("Got calculations: %s", {k: f"Total: {len(v)}, Min: {np.nanmin(v)}, "
                                                 f"Max: {np.nanmax(v)}, "
                                                 f"nans: {np.count_nonzero(np.isnan(v))}"
                                              for k, v in self.stats.items()
                                              if not k.startswith("raw")})