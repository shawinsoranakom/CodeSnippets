def _feed_extractor(self, loader: loader.Loader) -> None:
        """Process to feed the extractor from inside a thread

        Parameters
        ----------
        loader
            The loader for loading source images/video from disk
        """
        for media in loader.load():
            if self._input_thread.error_state.has_error:
                self._input_thread.error_state.re_raise()
            self._counts["face"] += len(media)

            if self._is_faces:
                assert media.frame_metadata is not None
                assert len(media) == 1
                needs_update = self._needs_update(media.frame_metadata.source_filename,
                                                  media.frame_metadata.face_index,
                                                  media.detected_faces[0])
            else:
                # To keep face indexes correct/cover off where only one face in an image is missing
                # a mask where there are multiple faces we process all faces again for any frames
                # which have missing masks.
                needs_update = any(self._needs_update(os.path.basename(media.filename),
                                                      idx,
                                                      detected_face)
                                   for idx, detected_face in enumerate(media.detected_faces))

            if not needs_update:
                logger.trace("No masks need updating in '%s'",  # type:ignore[attr-defined]
                             media.filename)
                continue

            logger.trace("Passing to extractor: '%s'", media.filename)  # type:ignore[attr-defined]
            self._extractor.put_media(media)

        logger.debug("Terminating loader thread")
        self._extractor.stop()