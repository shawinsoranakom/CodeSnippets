def _get_instance_labels(self, data: TensorDict, features: TensorDict,
                           labels: NestedTensorDict):
    """Generate the labels for text entity detection."""

    labels['instance_labels'] = {}
    # (1) Depending on `detection_unit`:
    #     Convert the word-id map to line-id map or use the word-id map directly
    # Word entity ids start from 1 in the map, so pad a -1 at the beginning of
    # the parent list to counter this offset.
    padded_parent = tf.concat(
        [tf.constant([-1]),
         tf.cast(data['groundtruth_parent'], tf.int32)], 0)
    if self._detection_unit == DetectionClass.WORD:
      entity_id_mask = data['resized_masks']
    elif self._detection_unit == DetectionClass.LINE:
      # The pixel value is entity_id + 1, shape = [H, W]; 0 for background.
      # correctness:
      # 0s in data['resized_masks'] --> padded_parent[0] == -1
      # i-th entity in plp.entities --> i+1 in data['resized_masks']
      #                             --> padded_parent[i+1]
      #                             --> data['groundtruth_parent'][i]
      #                             --> the parent of i-th entity
      entity_id_mask = tf.gather(padded_parent, data['resized_masks']) + 1
    elif self._detection_unit == DetectionClass.PARAGRAPH:
      # directly segmenting paragraphs; two hops here.
      entity_id_mask = tf.gather(padded_parent, data['resized_masks']) + 1
      entity_id_mask = tf.gather(padded_parent, entity_id_mask) + 1
    else:
      raise ValueError(f'No such detection unit: {self._detection_unit}')
    data['entity_id_mask'] = entity_id_mask

    # (2) Get individual masks for entities.
    entity_selection_mask = tf.equal(data['groundtruth_classes'],
                                     self._detection_unit)
    num_all_entity = utilities.resolve_shape(data['groundtruth_classes'])[0]
    # entity_ids is a 1-D tensor for IDs of all entities of a certain type.
    entity_ids = tf.boolean_mask(
        tf.range(num_all_entity, dtype=tf.int32), entity_selection_mask)  # (N,)
    # +1 to match the entity ids in entity_id_mask
    entity_ids = tf.reshape(entity_ids, (-1, 1, 1)) + 1
    individual_masks = tf.expand_dims(entity_id_mask, 0)
    individual_masks = tf.equal(entity_ids, individual_masks)  # (N, H, W), bool
    # TODO(longshangbang): replace with real mask sizes computing.
    # Currently, we use full-resolution masks for individual_masks. In order to
    # compute mask sizes, we need to convert individual_masks to int/float type.
    # This will cause OOM because the mask is too large.
    masks_sizes = tf.cast(
        tf.reduce_any(individual_masks, axis=[1, 2]), tf.float32)
    # remove empty masks (usually caused by cropping)
    non_empty_masks_ids = tf.not_equal(masks_sizes, 0)
    valid_masks = tf.boolean_mask(individual_masks, non_empty_masks_ids)
    valid_entity_ids = tf.boolean_mask(entity_ids, non_empty_masks_ids)[:, 0, 0]

    # (3) Write num of instance
    num_instance = tf.reduce_sum(tf.cast(non_empty_masks_ids, tf.float32))
    num_instance_and_bkg = num_instance + 1
    if self._max_num_instance >= 0:
      num_instance_and_bkg = tf.minimum(num_instance_and_bkg,
                                        self._max_num_instance)
    labels['instance_labels']['num_instance'] = num_instance_and_bkg

    # (4) Write instance masks
    num_entity_int = tf.cast(num_instance, tf.int32)
    max_num_entities = self._max_num_instance - 1  # Spare 1 for bkg.
    pad_num = tf.maximum(max_num_entities - num_entity_int, 0)
    padded_valid_masks = tf.pad(valid_masks, [[0, pad_num], [0, 0], [0, 0]])

    # If there are more instances than allowed, randomly sample some.
    # `random_selection_mask` is a 0/1 array; the maximum number of 1 is
    # `self._max_num_instance`; if not bound, it's an array with all 1s.
    if self._max_num_instance >= 0:
      padded_size = num_entity_int + pad_num
      random_selection = tf.random.uniform((padded_size,), dtype=tf.float32)
      selected_indices = tf.math.top_k(random_selection, k=max_num_entities)[1]
      random_selection_mask = tf.scatter_nd(
          indices=tf.expand_dims(selected_indices, axis=-1),
          updates=tf.ones((max_num_entities,), dtype=tf.bool),
          shape=(padded_size,))
    else:
      random_selection_mask = tf.ones((num_entity_int,), dtype=tf.bool)
    random_discard_mask = tf.logical_not(random_selection_mask)

    kept_masks = tf.boolean_mask(padded_valid_masks, random_selection_mask)
    erased_masks = tf.boolean_mask(padded_valid_masks, random_discard_mask)
    erased_masks = tf.cast(tf.reduce_any(erased_masks, axis=0), tf.float32)
    # erase text instances that are obmitted.
    features['images'] = _erase(erased_masks, features['images'], -1., 1.)
    labels['segmentation_output']['gt_word_score'] *= 1. - erased_masks
    kept_masks_and_bkg = tf.concat(
        [
            tf.math.logical_not(
                tf.reduce_any(kept_masks, axis=0, keepdims=True)),  # bkg
            kept_masks,
        ],
        0)
    labels['instance_labels']['masks'] = tf.argmax(kept_masks_and_bkg, axis=0)

    # (5) Write mask size
    # TODO(longshangbang): replace with real masks sizes
    masks_sizes = tf.cast(
        tf.reduce_any(kept_masks_and_bkg, axis=[1, 2]), tf.float32)
    labels['instance_labels']['masks_sizes'] = masks_sizes
    # (6) Write classes.
    classes = tf.ones((num_instance,), dtype=tf.int32)
    classes = tf.concat([tf.constant(2, tf.int32, (1,)), classes], 0)  # bkg
    if self._max_num_instance >= 0:
      classes = utilities.truncate_or_pad(classes, self._max_num_instance, 0)
    labels['instance_labels']['classes'] = classes

    # (7) gt-weights
    selected_ids = tf.boolean_mask(valid_entity_ids,
                                   random_selection_mask[:num_entity_int])

    if self._detection_unit != DetectionClass.PARAGRAPH:
      gt_text = tf.gather(data['groundtruth_text'], selected_ids - 1)
      gt_weights = tf.cast(tf.strings.length(gt_text) > 0, tf.float32)
    else:
      text_types = tf.concat(
          [
              tf.constant([8]),
              tf.cast(data['groundtruth_content_type'], tf.int32),
              # TODO(longshangbang): temp solution for tfes with no para labels
              tf.constant(8, shape=(1000,)),
          ],
          0)
      para_types = tf.gather(text_types, selected_ids)

      gt_weights = tf.cast(
          tf.not_equal(para_types, NOT_ANNOTATED_ID), tf.float32)

    gt_weights = tf.concat([tf.constant(1., shape=(1,)), gt_weights], 0)  # bkg
    if self._max_num_instance >= 0:
      gt_weights = utilities.truncate_or_pad(
          gt_weights, self._max_num_instance, 0)
    labels['instance_labels']['gt_weights'] = gt_weights

    # (8) get paragraph label
    # In this step, an array `{p_i}` is generated. `p_i` is an integer that
    # indicates the group of paragraph which i-th text belongs to. `p_i` == -1
    # if this instance is non-text or it has no paragraph labels.
    # word -> line -> paragraph
    if self._detection_unit == DetectionClass.WORD:
      num_hop = 2
    elif self._detection_unit == DetectionClass.LINE:
      num_hop = 1
    elif self._detection_unit == DetectionClass.PARAGRAPH:
      num_hop = 0
    else:
      raise ValueError(f'No such detection unit: {self._detection_unit}. '
                       'Note that this error should have been raised in '
                       'previous lines, not here!')
    para_ids = tf.identity(selected_ids)  # == id in plp + 1
    for _ in range(num_hop):
      para_ids = tf.gather(padded_parent, para_ids) + 1

    text_types = tf.concat(
        [
            tf.constant([8]),
            tf.cast(data['groundtruth_content_type'], tf.int32),
            # TODO(longshangbang): tricks for tfes that have not para labels
            tf.constant(8, shape=(1000,)),
        ],
        0)
    para_types = tf.gather(text_types, para_ids)

    para_ids = para_ids - 1  # revert to id in plp.entities; -1 for no labels
    valid_para = tf.cast(tf.not_equal(para_types, NOT_ANNOTATED_ID), tf.int32)
    para_ids = valid_para * para_ids + (1 - valid_para) * (-1)
    para_ids = tf.concat([tf.constant([-1]), para_ids], 0)  # add bkg

    has_para_ids = tf.cast(tf.reduce_sum(valid_para) > 0, tf.float32)

    if self._max_num_instance >= 0:
      para_ids = utilities.truncate_or_pad(
          para_ids, self._max_num_instance, 0, -1)
    labels['paragraph_labels'] = {
        'paragraph_ids': para_ids,
        'has_para_ids': has_para_ids
    }