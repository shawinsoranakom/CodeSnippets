def _rekey_examples(self, tfrecord_entry):
    serialized_example = copy.deepcopy(tfrecord_entry)

    input_example = tf.train.Example.FromString(serialized_example)

    self._num_images_found.inc(1)

    if self._reduce_image_size:
      input_example = self._resize_image(input_example)
      self._num_images_resized.inc(1)

    new_key = input_example.features.feature[
        self._sequence_key].bytes_list.value[0]

    if self._time_horizon:
      date_captured = datetime.datetime.strptime(
          six.ensure_str(input_example.features.feature[
              'image/date_captured'].bytes_list.value[0]), '%Y-%m-%d %H:%M:%S')
      year = date_captured.year
      month = date_captured.month
      day = date_captured.day
      week = np.floor(float(day) / float(7))
      hour = date_captured.hour
      minute = date_captured.minute

      if self._time_horizon == 'year':
        new_key = new_key + six.ensure_binary('/' + str(year))
      elif self._time_horizon == 'month':
        new_key = new_key + six.ensure_binary(
            '/' + str(year) + '/' + str(month))
      elif self._time_horizon == 'week':
        new_key = new_key + six.ensure_binary(
            '/' + str(year) + '/' + str(month) + '/' + str(week))
      elif self._time_horizon == 'day':
        new_key = new_key + six.ensure_binary(
            '/' + str(year) + '/' + str(month) + '/' + str(day))
      elif self._time_horizon == 'hour':
        new_key = new_key + six.ensure_binary(
            '/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + (
                str(hour)))
      elif self._time_horizon == 'minute':
        new_key = new_key + six.ensure_binary(
            '/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + (
                str(hour) + '/' + str(minute)))

    self._num_examples_processed.inc(1)

    return [(new_key, input_example)]