def _add_embeds_to_plugin(self, embeds: dict[str, npt.NDArray[np.float32]]) -> None:
        """Validate that we have exactly one embedding per image and add to the identity filter

        Parameters
        ----------
        embeds
            The file name with embeddings to add to the plugin filter
        """
        for is_filter, file_list in zip((True, False), (self._filter_files, self._nfilter_files)):
            if not file_list:
                continue
            collated: list[npt.NDArray[np.float32]] = []
            name = "Filter" if is_filter else "nFilter"
            for fname in file_list:
                embed = embeds.pop(fname)
                if not np.any(embed):
                    logger.warning("%s file '%s' contains no detected faces. Skipping",
                                   name, os.path.basename(fname))
                    continue
                if embed.ndim != 1 and is_filter:
                    logger.warning("%s file '%s' contains %s detected faces. Skipping",
                                   name, os.path.basename(fname), embed.shape[0])
                    continue
                if embed.ndim != 1 and not is_filter:
                    logger.warning("%s file '%s' contains %s detected faces. All of "
                                   "these identities will be used",
                                   name, os.path.basename(fname), embed.shape[0])
                    collated.extend(list(embed))
                    continue
                collated.append(embed)
            if not collated:
                logger.error("None of the provided %s files are valid.", name)
                sys.exit(1)
            logger.info("Adding %s face%s to Identity %s",
                        len(collated), "s" if len(collated) > 1 else "", name)
            T.cast(Identity, self._runner.handler).add_filter_identities(
                np.stack(collated, dtype="float32"), is_filter)