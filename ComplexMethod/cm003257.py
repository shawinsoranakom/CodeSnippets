def post_process_keypoint_matching(
        self,
        outputs: "LightGlueKeypointMatchingOutput",
        target_sizes: TensorType | list[tuple],
        threshold: float = 0.0,
    ) -> list[dict[str, "torch.Tensor"]]:
        """
        Converts the raw output of [`LightGlueKeypointMatchingOutput`] into lists of keypoints, scores and descriptors
        with coordinates absolute to the original image sizes.
        Args:
            outputs ([`LightGlueKeypointMatchingOutput`]):
                Raw outputs of the model.
            target_sizes (`torch.Tensor` or `list[tuple[tuple[int, int]]]`, *optional*):
                Tensor of shape `(batch_size, 2, 2)` or list of tuples of tuples (`tuple[int, int]`) containing the
                target size `(height, width)` of each image in the batch. This must be the original image size (before
                any processing).
            threshold (`float`, *optional*, defaults to `0.0`):
                Threshold to filter out the matches with low scores.
        Returns:
            `list[Dict]`: A list of dictionaries, each dictionary containing the keypoints in the first and second image
            of the pair, the matching scores and the matching indices.
        """
        import torch

        if outputs.mask.shape[0] != len(target_sizes):
            raise ValueError("Make sure that you pass in as many target sizes as the batch dimension of the mask")
        if not all(len(target_size) == 2 for target_size in target_sizes):
            raise ValueError("Each element of target_sizes must contain the size (h, w) of each image of the batch")

        if isinstance(target_sizes, list):
            image_pair_sizes = torch.tensor(target_sizes, device=outputs.mask.device)
        else:
            if target_sizes.shape[1] != 2 or target_sizes.shape[2] != 2:
                raise ValueError(
                    "Each element of target_sizes must contain the size (h, w) of each image of the batch"
                )
            image_pair_sizes = target_sizes

        keypoints = outputs.keypoints.clone()
        keypoints = keypoints * image_pair_sizes.flip(-1).reshape(-1, 2, 1, 2)
        keypoints = keypoints.to(torch.int32)

        results = []
        for mask_pair, keypoints_pair, matches, scores in zip(
            outputs.mask, keypoints, outputs.matches[:, 0], outputs.matching_scores[:, 0]
        ):
            mask0 = mask_pair[0] > 0
            mask1 = mask_pair[1] > 0
            keypoints0 = keypoints_pair[0][mask0]
            keypoints1 = keypoints_pair[1][mask1]
            matches0 = matches[mask0]
            scores0 = scores[mask0]

            # Filter out matches with low scores, invalid matches, and out-of-bounds indices
            valid_matches = (scores0 > threshold) & (matches0 > -1) & (matches0 < keypoints1.shape[0])

            matched_keypoints0 = keypoints0[valid_matches]
            matched_keypoints1 = keypoints1[matches0[valid_matches]]
            matching_scores = scores0[valid_matches]

            results.append(
                {
                    "keypoints0": matched_keypoints0,
                    "keypoints1": matched_keypoints1,
                    "matching_scores": matching_scores,
                }
            )

        return results