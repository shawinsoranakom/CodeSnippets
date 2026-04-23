def predict(self, batch: np.ndarray) -> np.ndarray:
        """Run inference on a PyTorch model.

        Parameters
        ----------
        batch
            The batch array to feed to the PyTorch model

        Returns
        -------
        The result from the PyTorch model
        """
        if self._model is None:
            raise ValueError("Plugin function 'load_torch_model' must have been called to use "
                             "this function")

        with torch.inference_mode():
            if self._use_pinned:
                feed = torch.from_numpy(batch).pin_memory().to(self.device,
                                                               non_blocking=True,
                                                               memory_format=torch.channels_last)
            else:
                feed = torch.from_numpy(batch).to(self.device, memory_format=torch.channels_last)
            out = self._model(feed)

            if not self._first_batch_seen:
                self._process_first_batch(out)

            if self._return_indices:
                out = itemgetter(*self._return_indices)(out)

            out = [x.to("cpu").numpy()
                   for x in out] if self._output_is_list else out.to("cpu").numpy()

        if self._output_is_list:
            retval = np.empty((self._output_length, ), dtype="object")
            retval[:] = out
            return retval
        return T.cast(np.ndarray, out)