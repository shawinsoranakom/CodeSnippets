def _get_erosion_kernels(self, mask: np.ndarray) -> list[np.ndarray]:
        """ Get the erosion kernels for each of the center, left, top right and bottom erosions.

        An approximation is made based on the number of positive pixels within the mask to create
        an ellipse to act as kernel.

        Parameters
        ----------
        mask : :class:`numpy.ndarray`
            The mask to be eroded or dilated

        Returns
        -------
        list[:class:`numpy.ndarray`]
            The erosion kernels to be used for erosion/dilation
        """
        mask_radius = np.sqrt(np.sum(mask)) / 2
        kernel_sizes = [max(0, int(abs(ratio * mask_radius))) for ratio in self._erodes]
        kernels = []
        for idx, size in enumerate(kernel_sizes):
            kernel = [size, size]
            shape = cv2.MORPH_ELLIPSE if idx == 0 else cv2.MORPH_RECT
            if idx > 1:
                pos = 0 if idx % 2 == 0 else 1
                kernel[pos] = 1  # Set x/y to 1px based on whether eroding top/bottom, left/right
            kernels.append(cv2.getStructuringElement(shape, kernel) if size else np.array(0))
        logger.trace("Erosion kernels: %s", [k.shape for k in kernels])  # type: ignore
        return kernels