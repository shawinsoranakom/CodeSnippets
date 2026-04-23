def mask(self) -> np.ndarray:
        """The mask at the size of :attr:`stored_size` with any requested blurring, threshold
        amount and centering applied."""
        mask = self.stored_mask
        if self._dilation[-1] is not None or self._threshold != 0.0 or self._blur_kernel != 0:
            mask = mask.copy()
        self._dilate_mask(mask)
        if self._threshold != 0.0:
            mask[mask < self._threshold] = 0.0
            mask[mask > 255.0 - self._threshold] = 255.0
        if self._blur_kernel != 0 and self._blur_type is not None:
            mask = BlurMask(self._blur_type,
                            mask,
                            self._blur_kernel,
                            passes=self._blur_passes).blurred
        if self._sub_crop_size:  # Crop the mask to the given centering
            out = np.zeros((self._sub_crop_size, self._sub_crop_size, 1), dtype=mask.dtype)
            slice_in, slice_out = self._sub_crop_slices["in"], self._sub_crop_slices["out"]
            out[slice_out[0], slice_out[1], :] = mask[slice_in[0], slice_in[1], :]
            mask = out
        logger.trace("mask shape: %s", mask.shape)  # type:ignore[attr-defined]
        return mask