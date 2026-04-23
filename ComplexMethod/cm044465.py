def get_embeddings(self, pipeline: ExtractRunner) -> None:
        """Obtain the embeddings that are to be used for face filtering and add to the identity
        plugin

        Parameters
        ----------
        pipeline
            The extraction pipelines for obtaining embeddings from non-faceswap images
        """
        embeds: dict[str, npt.NDArray[np.float32]] = {}
        non_aligned: dict[str, npt.NDArray[np.uint8]] = {}
        aligned: dict[str, tuple[PNGHeader, npt.NDArray[np.uint8]]] = {}

        for filepath in self._filter_files.union(self._nfilter_files):
            with open(filepath, "rb") as in_file:
                raw_image = in_file.read()

            meta = self._get_meta(filepath, raw_image)
            if meta is not None:
                idn = meta.alignments.identity
                embed = np.array(idn.get(self._runner.handler.storage_name, []),
                                 dtype="float32")
                if np.any(embed):
                    logger.debug("[IdentityFilter] Identity from header '%s'. Shape: %s",
                                 filepath, embed.shape)
                    embeds[filepath] = embed
                    continue

            image = T.cast("npt.NDArray[np.uint8]",
                           cv2.imdecode(np.frombuffer(raw_image, dtype="uint8"), cv2.IMREAD_COLOR))

            if meta is None:
                non_aligned[filepath] = image
                continue

            logger.debug("[IdentityFilter] No identity in header: '%s'", filepath)
            aligned[filepath] = (meta, image)

        if aligned or non_aligned:
            logger.info("Extracting faces for Identity Filter...")
        if non_aligned:
            embeds |= self._from_pipeline(pipeline, non_aligned)
        if aligned:
            embeds |= self._from_plugin(aligned)
        self._add_embeds_to_plugin(embeds)