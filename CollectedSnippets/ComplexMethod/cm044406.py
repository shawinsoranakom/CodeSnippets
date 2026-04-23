def _validate(self) -> None:
        """Validate the Command Line Options.

        Ensure that certain cli selections are valid and won't result in an error. Checks:
            * If frames have been passed in with video output, ensure user supplies reference
            video.
            * If "on-the-fly" and a Neural Network mask is selected, warn and switch to 'extended'
            * If a mask-type is selected, ensure it exists in the alignments file.
            * If a predicted mask-type is selected, ensure model has been trained with a mask
            otherwise attempt to select first available masks, otherwise raise error.

        Raises
        ------
        FaceswapError
            If an invalid selection has been found.

        """
        if (self._args.writer == "ffmpeg" and
                not self._images.is_video and
                self._args.reference_video is None):
            raise FaceswapError("Output as video selected, but using frames as input. You must "
                                "provide a reference video ('-ref', '--reference-video').")

        if (self._args.on_the_fly and
                self._args.mask_type not in ("none", "extended", "components")):
            logger.warning("You have selected an incompatible mask type ('%s') for On-The-Fly "
                           "conversion. Switching to 'extended'", self._args.mask_type)
            self._args.mask_type = "extended"

        if (not self._args.on_the_fly and
                self._args.mask_type not in ("none", "predicted", "extended", "components") and
                not self._alignments.mask_is_valid(self._args.mask_type)):
            msg = (f"You have selected the Mask Type `{self._args.mask_type}` but at least one "
                   "face does not have this mask stored in the Alignments File.\nYou should "
                   "generate the required masks with the Mask Tool or set the Mask Type option to "
                   "an existing Mask Type.\nA summary of existing masks is as follows:\nTotal "
                   f"faces: {self._alignments.faces_count}, "
                   f"Masks: {self._alignments.mask_summary}")
            raise FaceswapError(msg)

        if self._args.mask_type == "predicted" and not self._predictor.has_predicted_mask:
            available_masks = [k for k, v in self._alignments.mask_summary.items()
                               if k != "none" and v == self._alignments.faces_count]
            if not available_masks:
                msg = ("Predicted Mask selected, but the model was not trained with a mask and no "
                       "masks are stored in the Alignments File.\nYou should generate the "
                       "required masks with the Mask Tool or set the Mask Type to `none`.")
                raise FaceswapError(msg)
            mask_type = available_masks[0]
            logger.warning("Predicted Mask selected, but the model was not trained with a "
                           "mask. Selecting first available mask: '%s'", mask_type)
            self._args.mask_type = mask_type