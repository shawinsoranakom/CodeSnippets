def decode(self, tf_example_string_tensor: tf.string):
    """Decodes serialized tensorflow example and returns a tensor dictionary.

    Args:
      tf_example_string_tensor: A string tensor holding a serialized tensorflow
        example proto.

    Returns:
      A dictionary contains a subset of the following, depends on the inputs:
        image: A uint8 tensor of shape [height, width, 3] containing the image.
        source_id: A string tensor contains image fingerprint.
        key: A string tensor contains the unique sha256 hash key.
        label_type: Either `full` or `partial`. `full` means all the text are
          fully labeled, `partial` otherwise. Currently, this is used by E2E
          model. If an input image is fully labeled, we update the weights of
          both the detection and the recognizer. Otherwise, only recognizer part
          of the model is trained.
        groundtruth_text: A string tensor list, the original transcriptions.
        groundtruth_encoded_text: A string tensor list, the class ids for the
          atoms in the text, after applying the reordering algorithm, in string
          form. For example "90,71,85,69,86,85,93,90,71,91,1,71,85,93,90,71".
          This depends on the class label map provided to the conversion
          program. These are 0 based, with -1 for OOV symbols.
        groundtruth_classes: A int32 tensor of shape [num_boxes] contains the
          class id. Note this is 1 based, 0 is reserved for background class.
        groundtruth_content_type: A int32 tensor of shape [num_boxes] contains
          the content type. Values correspond to PageLayoutEntity::ContentType.
        groundtruth_weight: A int32 tensor of shape [num_boxes], either 0 or 1.
          If a region has weight 0, it will be ignored when computing the
          losses.
        groundtruth_boxes: A float tensor of shape [num_boxes, 5] contains the
          groundtruth rotated rectangles. Each row is in [left, top, box_width,
          box_height, angle] order, absolute coordinates are used.
        groundtruth_aligned_boxes: A float tensor of shape [num_boxes, 4]
          contains the groundtruth axis-aligned rectangles. Each row is in
          [ymin, xmin, ymax, xmax] order. Currently, this is used to store
          groundtruth symbol boxes.
        groundtruth_vertices: A string tensor list contains encoded normalized
          box or polygon coordinates. E.g. `x1,y1,x2,y2,x3,y3,x4,y4`.
        groundtruth_instance_masks: A float tensor of shape [num_boxes, height,
          width] contains binarized image sized instance segmentation masks.
          `1.0` for positive region, `0.0` otherwise. None if not in tfe.
        frame_id: A int32 tensor of shape [num_boxes], either `0` or `1`.
          `0` means object comes from first image, `1` means second.
        track_id: A int32 tensor of shape [num_boxes], where value indicates
          identity across frame indices.
        additional_channels: A uint8 tensor of shape [H, W, C] representing some
          features.
    """
    parsed_tensors = tf.io.parse_single_example(
        serialized=tf_example_string_tensor, features=self.keys_to_features)
    for k in parsed_tensors:
      if isinstance(parsed_tensors[k], tf.SparseTensor):
        if parsed_tensors[k].dtype == tf.string:
          parsed_tensors[k] = tf.sparse.to_dense(
              parsed_tensors[k], default_value='')
        else:
          parsed_tensors[k] = tf.sparse.to_dense(
              parsed_tensors[k], default_value=0)

    decoded_tensors = {}
    decoded_tensors.update(self._decode_image(parsed_tensors))
    decoded_tensors.update(self._decode_rboxes(parsed_tensors))
    decoded_tensors.update(self._decode_boxes(parsed_tensors))
    if self._use_instance_mask:
      decoded_tensors[
          'groundtruth_instance_masks'] = self._decode_png_instance_masks(
              parsed_tensors)
    if self._num_additional_channels:
      decoded_tensors.update(self._decode_additional_channels(
          parsed_tensors, self._num_additional_channels))

    # other attributes:
    for key in self.name_to_key:
      if key not in decoded_tensors:
        decoded_tensors[key] = parsed_tensors[self.name_to_key[key]]

    if 'groundtruth_instance_masks' not in decoded_tensors:
      decoded_tensors['groundtruth_instance_masks'] = None

    return decoded_tensors