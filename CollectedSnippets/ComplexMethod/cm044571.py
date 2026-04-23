def binning(self) -> list[list[str]]:
        """ Group into bins by CNN face similarity

        Returns
        -------
        list
            List of bins of filenames
        """
        msg = "dissimilarity" if self._is_dissim else "similarity"
        logger.info("Grouping by face-cnn %s...", msg)

        # Groups are of the form: group_num -> reference faces
        reference_groups: dict[int, list[np.ndarray]] = {}

        # Bins array, where index is the group number and value is
        # an array containing the file paths to the images in that group.
        bins: list[list[str]] = []

        # Comparison threshold used to decide how similar
        # faces have to be to be grouped together.
        # It is multiplied by 1000 here to allow the cli option to use smaller
        # numbers.
        threshold = self._threshold * 1000
        img_list_len = len(self._result)

        for i in tqdm(range(0, img_list_len - 1),
                      desc="Grouping",
                      file=sys.stdout,
                      leave=False):
            fl1 = self._result[i][1]

            current_key = -1
            current_score = float("inf")

            for key, references in reference_groups.items():
                try:
                    score = self._get_avg_score(fl1,  # pyright:ignore[reportArgumentType]
                                                references)
                except TypeError:
                    score = float("inf")
                except ZeroDivisionError:
                    score = float("inf")
                if score < current_score:
                    current_key, current_score = key, score

            if current_score < threshold:
                reference_groups[current_key].append(fl1[0])  # pyright:ignore[reportIndexIssue]
                bins[current_key].append(self._result[i][0])
            else:
                reference_groups[len(reference_groups)] = [self._result[i][1]]  # pyright:ignore
                bins.append([self._result[i][0]])

        return bins