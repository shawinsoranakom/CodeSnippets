def _get_input_locations(cls, input_location: str, batch_mode: bool) -> list[str]:
        """ Obtain the full path to input locations. Will be a list of locations if batch mode is
        selected, or a list containing a single location if batch mode is not selected.

        Parameters
        ----------
        input_location
            The full path to the input location. Either a video file, a folder of images or a
            folder containing either/or videos and sub-folders of images (if batch mode is
            selected)
        batch_mode
            ``True`` if extract is running in batch mode

        Returns
        -------
        The list of input location paths
        """
        if not batch_mode:
            return [input_location]

        if os.path.isfile(input_location):
            logger.warning("Batch mode selected but input is not a folder. Switching to normal "
                           "mode")
            return [input_location]

        retval = [os.path.join(input_location, fname)
                  for fname in os.listdir(input_location)
                  if (os.path.isdir(os.path.join(input_location, fname))  # folder images
                      and any(os.path.splitext(iname)[-1].lower() in IMAGE_EXTENSIONS
                              for iname in os.listdir(os.path.join(input_location, fname))))
                  or os.path.splitext(fname)[-1].lower() in VIDEO_EXTENSIONS]  # video

        retval = list(sorted(retval))
        logger.debug("[Extract] Input locations: %s", retval)
        return retval