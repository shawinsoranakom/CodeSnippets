def _run_inference_and_generate_embedding(self, tfexample_key_value):
    key, tfexample = tfexample_key_value
    input_example = tf.train.Example.FromString(tfexample)
    example = tf.train.Example()
    example.CopyFrom(input_example)

    try:
      date_captured = get_date_captured(input_example)
      unix_time = ((date_captured -
                    datetime.datetime.fromtimestamp(0)).total_seconds())
      example.features.feature['image/unix_time'].float_list.value.extend(
          [unix_time])
      temporal_embedding = embed_date_captured(date_captured)
    except Exception:  # pylint: disable=broad-except
      temporal_embedding = None

    detections = self._detect_fn.signatures['serving_default'](
        (tf.expand_dims(tf.convert_to_tensor(tfexample), 0)))
    if self._embedding_type == 'final_box_features':
      detection_features = detections['detection_features']
    elif self._embedding_type == 'rpn_box_features':
      detection_features = detections['cropped_rpn_box_features']
    else:
      raise ValueError('embedding type not supported')
    detection_boxes = detections['detection_boxes']
    num_detections = detections['num_detections']
    detection_scores = detections['detection_scores']

    num_detections = int(num_detections)
    embed_all = []
    score_all = []

    detection_features = np.asarray(detection_features)

    embedding_count = 0
    for index in range(min(num_detections, self._top_k_embedding_count)):
      bb_embedding, score = get_bb_embedding(
          detection_features, detection_boxes, detection_scores, index)
      embed_all.extend(bb_embedding)
      if temporal_embedding is not None: embed_all.extend(temporal_embedding)
      score_all.append(score)
      embedding_count += 1

    for index in range(
        max(0, num_detections - 1),
        max(-1, num_detections - 1 - self._bottom_k_embedding_count), -1):
      bb_embedding, score = get_bb_embedding(
          detection_features, detection_boxes, detection_scores, index)
      embed_all.extend(bb_embedding)
      if temporal_embedding is not None: embed_all.extend(temporal_embedding)
      score_all.append(score)
      embedding_count += 1

    if embedding_count == 0:
      bb_embedding, score = get_bb_embedding(
          detection_features, detection_boxes, detection_scores, 0)
      embed_all.extend(bb_embedding)
      if temporal_embedding is not None: embed_all.extend(temporal_embedding)
      score_all.append(score)

    # Takes max in case embedding_count is 0.
    embedding_length = len(embed_all) // max(1, embedding_count)

    embed_all = np.asarray(embed_all)

    example.features.feature['image/embedding'].float_list.value.extend(
        embed_all)
    example.features.feature['image/embedding_score'].float_list.value.extend(
        score_all)
    example.features.feature['image/embedding_length'].int64_list.value.append(
        embedding_length)
    example.features.feature['image/embedding_count'].int64_list.value.append(
        embedding_count)

    self._num_examples_processed.inc(1)
    return [(key, example)]