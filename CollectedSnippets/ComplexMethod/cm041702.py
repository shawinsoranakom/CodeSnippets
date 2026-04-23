def _find_medias(self, medias: Union["MediaType", list["MediaType"], None]) -> list["MediaType"] | None:
        r"""Optionally concatenate media path to media dir when loading from local disk."""
        if medias is None:
            return None
        elif not isinstance(medias, list):
            medias = [medias]
        elif len(medias) == 0:
            return None
        else:
            medias = medias[:]

        if self.dataset_attr.load_from in ["script", "file"]:
            if isinstance(medias[0], str):
                for i in range(len(medias)):
                    media_path = os.path.join(self.data_args.media_dir, medias[i])
                    if os.path.isfile(media_path):
                        medias[i] = media_path
                    else:
                        logger.warning_rank0_once(
                            f"Media {medias[i]} does not exist in `media_dir`. Use original path."
                        )
            elif isinstance(medias[0], list):  # for processed video frames
                # medias is a list of lists, e.g., [[frame1.jpg, frame2.jpg], [frame3.jpg, frame4.jpg]]
                for i in range(len(medias)):
                    for j in range(len(medias[i])):
                        media_path = os.path.join(self.data_args.media_dir, medias[i][j])
                        if os.path.isfile(media_path):
                            medias[i][j] = media_path
                        else:
                            logger.warning_rank0_once(
                                f"Media {medias[i][j]} does not exist in `media_dir`. Use original path."
                            )

        return medias