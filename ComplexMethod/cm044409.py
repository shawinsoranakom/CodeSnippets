def _save(self, completion_event: Event) -> None:
        """Save the converted images.

        Puts the selected writer into a background thread and feeds it from the output of the
        patch queue.

        Parameters
        ----------
        completion_event
            An event that this process triggers when it has finished saving
        """
        logger.debug("Save Images: Start")
        write_preview = self._args.redirect_gui and self._writer.is_stream
        preview_image = os.path.join(self._writer.output_folder, ".gui_preview.jpg")
        logger.debug("Write preview for gui: %s", write_preview)
        for idx in tqdm(range(self._total_count), desc="Converting", file=sys.stdout):
            if self._queues["save"].shutdown_event.is_set():
                logger.debug("Save Queue: Stop signal received. Terminating")
                break
            item: tuple[str, np.ndarray | bytes] | T.Literal["EOF"] = self._queues["save"].get()
            if item == "EOF":
                logger.debug("EOF Received")
                break
            filename, image = item
            # Write out preview image for the GUI every 10 frames if writing to stream
            if write_preview and idx % 10 == 0 and not os.path.exists(preview_image):
                logger.debug("Writing GUI Preview image: '%s'", preview_image)
                assert isinstance(image, np.ndarray)
                cv2.imwrite(preview_image, image)
            self._writer.write(filename, image)
        self._writer.close()
        if self._extractor is not None:
            self._extractor.stop()
        completion_event.set()
        logger.debug("Save Faces: Complete")