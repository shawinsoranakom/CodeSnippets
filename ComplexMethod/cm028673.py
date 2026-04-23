def wait_for_new_savedmodel(
      self,
      last_savedmodel: Optional[str] = None,
      seconds_to_sleep: float = 1.0,
      timeout: Optional[float] = None) -> Union[str, None]:
    """Waits until a new savedmodel file is found.

    Args:
      last_savedmodel: The last savedmodel path used or `None` if we're
        expecting a savedmodel for the first time.
      seconds_to_sleep: The number of seconds to sleep for before looking for a
        new savedmodel.
      timeout: The maximum number of seconds to wait. If left as `None`, then
        the process will wait indefinitely.

    Returns:
      A new savedmodel path, or None if the timeout was reached.
    """
    logging.info('Waiting for new savedmodel at %s', self._directory)
    stop_time = time.time() + timeout if timeout is not None else None

    last_savedmodel_number = -1
    if last_savedmodel:
      last_savedmodel_number = self.get_savedmodel_number_from_path(
          last_savedmodel)

    while True:
      if stop_time is not None and time.time() + seconds_to_sleep > stop_time:
        return None

      existing_savedmodels = {}
      for savedmodel_path in self.get_existing_savedmodels():
        savedmodel_number = self.get_savedmodel_number_from_path(
            savedmodel_path)
        if savedmodel_number is not None:
          existing_savedmodels[savedmodel_number] = savedmodel_path

      # Find the first savedmodel with larger step number as next savedmodel.
      savedmodel_path = None
      existing_savedmodels = dict(sorted(existing_savedmodels.items()))
      for savedmodel_number in existing_savedmodels:
        if savedmodel_number > last_savedmodel_number:
          savedmodel_path = existing_savedmodels[savedmodel_number]
          break

      if savedmodel_path:
        logging.info('Found new savedmodel at %s', savedmodel_path)
        return savedmodel_path
      else:
        time.sleep(seconds_to_sleep)