def _add_context_to_example(self, grouped_entry):
    key, example_collection = grouped_entry
    list_of_examples = []

    example_list = list(example_collection)

    if self._add_context_features:
      context_features, feature_length, context_features_image_id_list = (
          self._build_context_features(example_list))

    if self._image_ids_to_keep is not None:
      new_example_list = []
      for example in example_list:
        im_id = example.features.feature['image/source_id'].bytes_list.value[0]
        self._images_loaded.inc(1)
        if six.ensure_str(im_id) in self._image_ids_to_keep:
          self._images_kept.inc(1)
          new_example_list.append(example)
      if new_example_list:
        example_list = new_example_list
      else:
        return []

    if self._output_type == 'tf_sequence_example':
      if self._max_clip_length is not None:
        # For now, no overlap
        clips = get_sliding_window(
            example_list, self._max_clip_length, self._max_clip_length)
      else:
        clips = [example_list]

      for clip_num, clip_list in enumerate(clips):
        # initialize sequence example
        seq_example = tf.train.SequenceExample()
        video_id = six.ensure_str(key)+'_'+ str(clip_num)
        seq_example.context.feature['clip/media_id'].bytes_list.value.append(
            video_id.encode('utf8'))
        seq_example.context.feature['clip/frames'].int64_list.value.append(
            len(clip_list))

        seq_example.context.feature[
            'clip/start/timestamp'].int64_list.value.append(0)
        seq_example.context.feature[
            'clip/end/timestamp'].int64_list.value.append(len(clip_list))
        seq_example.context.feature['image/format'].bytes_list.value.append(
            six.ensure_binary('JPG'))
        seq_example.context.feature['image/channels'].int64_list.value.append(3)
        context_example = clip_list[0]
        seq_example.context.feature['image/height'].int64_list.value.append(
            context_example.features.feature[
                'image/height'].int64_list.value[0])
        seq_example.context.feature['image/width'].int64_list.value.append(
            context_example.features.feature['image/width'].int64_list.value[0])

        seq_example.context.feature[
            'image/context_feature_length'].int64_list.value.append(
                feature_length)
        seq_example.context.feature[
            'image/context_features'].float_list.value.extend(
                context_features)
        if self._keep_context_features_image_id_list:
          seq_example.context.feature[
              'image/context_features_image_id_list'].bytes_list.value.extend(
                  context_features_image_id_list)

        encoded_image_list = seq_example.feature_lists.feature_list[
            'image/encoded']
        timestamps_list = seq_example.feature_lists.feature_list[
            'image/timestamp']
        context_features_idx_list = seq_example.feature_lists.feature_list[
            'image/context_features_idx']
        date_captured_list = seq_example.feature_lists.feature_list[
            'image/date_captured']
        unix_time_list = seq_example.feature_lists.feature_list[
            'image/unix_time']
        location_list = seq_example.feature_lists.feature_list['image/location']
        image_ids_list = seq_example.feature_lists.feature_list[
            'image/source_id']
        gt_xmin_list = seq_example.feature_lists.feature_list[
            'region/bbox/xmin']
        gt_xmax_list = seq_example.feature_lists.feature_list[
            'region/bbox/xmax']
        gt_ymin_list = seq_example.feature_lists.feature_list[
            'region/bbox/ymin']
        gt_ymax_list = seq_example.feature_lists.feature_list[
            'region/bbox/ymax']
        gt_type_list = seq_example.feature_lists.feature_list[
            'region/label/index']
        gt_type_string_list = seq_example.feature_lists.feature_list[
            'region/label/string']
        gt_is_annotated_list = seq_example.feature_lists.feature_list[
            'region/is_annotated']

        for idx, example in enumerate(clip_list):

          encoded_image = encoded_image_list.feature.add()
          encoded_image.bytes_list.value.extend(
              example.features.feature['image/encoded'].bytes_list.value)

          image_id = image_ids_list.feature.add()
          image_id.bytes_list.value.append(
              example.features.feature['image/source_id'].bytes_list.value[0])

          timestamp = timestamps_list.feature.add()
          # Timestamp is currently order in the list.
          timestamp.int64_list.value.extend([idx])

          context_features_idx = context_features_idx_list.feature.add()
          context_features_idx.int64_list.value.extend(
              example.features.feature['context_features_idx'].int64_list.value)

          date_captured = date_captured_list.feature.add()
          date_captured.bytes_list.value.extend(
              example.features.feature['image/date_captured'].bytes_list.value)
          unix_time = unix_time_list.feature.add()
          unix_time.float_list.value.extend(
              example.features.feature['image/unix_time'].float_list.value)
          location = location_list.feature.add()
          location.bytes_list.value.extend(
              example.features.feature['image/location'].bytes_list.value)

          gt_xmin = gt_xmin_list.feature.add()
          gt_xmax = gt_xmax_list.feature.add()
          gt_ymin = gt_ymin_list.feature.add()
          gt_ymax = gt_ymax_list.feature.add()
          gt_type = gt_type_list.feature.add()
          gt_type_str = gt_type_string_list.feature.add()

          gt_is_annotated = gt_is_annotated_list.feature.add()
          gt_is_annotated.int64_list.value.append(1)

          gt_xmin.float_list.value.extend(
              example.features.feature[
                  'image/object/bbox/xmin'].float_list.value)
          gt_xmax.float_list.value.extend(
              example.features.feature[
                  'image/object/bbox/xmax'].float_list.value)
          gt_ymin.float_list.value.extend(
              example.features.feature[
                  'image/object/bbox/ymin'].float_list.value)
          gt_ymax.float_list.value.extend(
              example.features.feature[
                  'image/object/bbox/ymax'].float_list.value)

          gt_type.int64_list.value.extend(
              example.features.feature[
                  'image/object/class/label'].int64_list.value)
          gt_type_str.bytes_list.value.extend(
              example.features.feature[
                  'image/object/class/text'].bytes_list.value)

        self._num_examples_processed.inc(1)
        list_of_examples.append(seq_example)

    elif self._output_type == 'tf_example':

      for example in example_list:
        im_id = example.features.feature['image/source_id'].bytes_list.value[0]

        if self._add_context_features:
          example.features.feature[
              'image/context_features'].float_list.value.extend(
                  context_features)
          example.features.feature[
              'image/context_feature_length'].int64_list.value.append(
                  feature_length)

        if self._keep_context_features_image_id_list:
          example.features.feature[
              'image/context_features_image_id_list'].bytes_list.value.extend(
                  context_features_image_id_list)

        self._num_examples_processed.inc(1)
        list_of_examples.append(example)

    return list_of_examples