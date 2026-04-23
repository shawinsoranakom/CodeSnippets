def _erode(self, mask: np.ndarray) -> np.ndarray:
        """ Erode or dilate mask the mask based on configuration options.

        Parameters
        ----------
        mask : :class:`numpy.ndarray`
            The mask to be eroded or dilated

        Returns
        -------
        :class:`numpy.ndarray`
            The mask with erosion/dilation applied
        """
        kernels = self._get_erosion_kernels(mask)
        if not any(k.any() for k in kernels):
            return mask  # No kernels could be created from selected input res
        eroded = mask
        for idx, (kernel, ratio) in enumerate(zip(kernels, self._erodes)):
            if not kernel.any():
                continue
            anchor = [-1, -1]
            if idx > 0:
                pos = 1 if idx % 2 == 0 else 0
                if ratio > 0:
                    val = max(kernel.shape) - 1 if idx < 3 else 0
                else:
                    val = 0 if idx < 3 else max(kernel.shape) - 1
                anchor[pos] = val

            func = cv2.erode if ratio > 0 else cv2.dilate
            eroded = func(eroded, kernel, iterations=1, anchor=anchor)

        return eroded[..., None]