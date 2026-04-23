def process(self, batch: ExtractBatch) -> None:
        """Perform inference to get results from the aligner

        Parameters
        ----------
        batch
            The incoming ExtractBatch to use for processing
        """
        result = None
        for iteration in range(1, self._re_align.iterations + 1):
            is_final = iteration == self._re_align.iterations

            if is_final and self._re_align.enabled:
                # Need to get prepared aligned images from first-pass output
                self._prepare_data(batch, iteration=iteration)

            assert batch.data is not None
            result = self._get_predictions(is_final, batch.data)

            if is_final and not self._re_align.enabled:  # Nothing left to do. Just the 1 pass
                break

            if self._overridden["post_process"]:  # Must make sure we are final (B, 68, 2) lms
                result = self.plugin.post_process(result)

            self._re_align(batch, result, iteration)  # 1st or 2nd pass re-align op

        assert result is not None
        batch.data = result