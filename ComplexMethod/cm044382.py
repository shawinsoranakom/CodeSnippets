def _generate_priors(self, clip: bool = False  # pylint:disable=too-many-locals
                         ) -> npt.NDArray[np.float32]:
        """Generate the anchor boxes for the image size

        Parameters
        ----------
        clip
            ``True`` to clip the output to 0-1. Default: ``False``

        Returns
        -------
        The pre-computed priors in center-offset form shape: (1, num_priors, 4)
        """
        steps = [8, 16, 32]
        min_sizes = [[16, 32], [64, 128], [256, 512]]
        feature_maps = [[ceil(self.input_size / step), ceil(self.input_size / step)]
                        for step in steps]
        anchors = []

        for sizes, feats, step in zip(min_sizes, feature_maps, steps):
            for i, j in product(range(feats[0]), range(feats[1])):
                for min_size in sizes:
                    s_kx = min_size / self.input_size
                    s_ky = min_size / self.input_size
                    dense_cx = [x * step / self.input_size for x in [j + 0.5]]
                    dense_cy = [y * step / self.input_size for y in [i + 0.5]]
                    for cy, cx in product(dense_cy, dense_cx):
                        anchors += [cx, cy, s_kx, s_ky]

        output = np.array(anchors, dtype="float32").reshape(-1, 4)
        if clip:
            output.clip(0, 1)
        return output[None]