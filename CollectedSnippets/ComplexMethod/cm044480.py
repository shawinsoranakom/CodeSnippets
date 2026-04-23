def _update_viewers(self,  # pylint:disable=too-many-locals
                        viewer: Callable[[np.ndarray, str], None] | None,
                        do_timelapse: bool = False) -> None:
        """Update the preview viewer and timelapse output

        Parameters
        ----------
        viewer
            The function that will display the preview image
        do_timelapse
            ``True`` to generate a timelapse preview image
        """
        if (viewer is None or self._preview_loader is None) and not do_timelapse:
            return

        if do_timelapse:
            assert self._timelapse_loader is not None
            loader = self._timelapse_loader
        else:
            assert self._preview_loader is not None
            loader = self._preview_loader
        feed, target = next(loader)

        num_sides = feed.shape[0]
        ndim = 4 if mod_cfg.Loss.learn_mask() else 3
        predictions: npt.NDArray[np.float32] = np.empty((num_sides,
                                                         num_sides,
                                                         target.shape[1],
                                                         self._out_size,
                                                         self._out_size,
                                                         ndim),
                                                        dtype=np.float32)
        logger.debug("[Trainer] feed: %s, target: %s, predictions_holder: %s",
                     feed.shape, target.shape, predictions.shape)
        for side_idx in range(num_sides):
            rolled_feed = torch.roll(feed, shifts=side_idx, dims=0)
            pred = self._get_predictions(rolled_feed)
            for input_idx in range(num_sides):
                original_idx = (input_idx - side_idx) % num_sides
                predictions[original_idx, side_idx] = pred[input_idx]

        targets = target.cpu().numpy()
        if self._model.color_order == "rgb":
            predictions[..., :3] = predictions[..., 2::-1]
            targets[..., :3] = targets[..., 2::-1]
        logger.debug("[Trainer] Got preview images: predictions: %s, targets: %s",
                     format_array(predictions), format_array(targets))

        samples = self._samples.get_preview(predictions, targets)

        if do_timelapse:
            filename = os.path.join(self._timelapse_output, str(int(time.time())) + ".jpg")
            cv2.imwrite(filename, samples)
            logger.debug("[Trainer] Created time-lapse: '%s'", filename)
            return

        if viewer is not None:
            viewer(samples,
                   "Training - 'S': Save Now. 'R': Refresh Preview. 'M': Toggle Mask. 'F': "
                   "Toggle Screen Fit-Actual Size. 'ENTER': Save and Quit")