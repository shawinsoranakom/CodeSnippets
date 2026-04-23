def _single_image_nms_fn(args):
      """Runs NMS on a single image and returns padded output.

      Args:
        args: A list of tensors consisting of the following:
          per_image_boxes - A [num_anchors, q, 4] float32 tensor containing
            detections. If `q` is 1 then same boxes are used for all classes
            otherwise, if `q` is equal to number of classes, class-specific
            boxes are used.
          per_image_scores - A [num_anchors, num_classes] float32 tensor
            containing the scores for each of the `num_anchors` detections.
          per_image_masks - A [num_anchors, q, mask_height, mask_width] float32
            tensor containing box masks. `q` can be either number of classes
            or 1 depending on whether a separate mask is predicted per class.
          per_image_clip_window - A 1D float32 tensor of the form
            [ymin, xmin, ymax, xmax] representing the window to clip the boxes
            to.
          per_image_additional_fields - (optional) A variable number of float32
            tensors each with size [num_anchors, ...].
          per_image_num_valid_boxes - A tensor of type `int32`. A 1-D tensor of
            shape [batch_size] representing the number of valid boxes to be
            considered for each image in the batch.  This parameter allows for
            ignoring zero paddings.

      Returns:
        'nmsed_boxes': A [max_detections, 4] float32 tensor containing the
          non-max suppressed boxes.
        'nmsed_scores': A [max_detections] float32 tensor containing the scores
          for the boxes.
        'nmsed_classes': A [max_detections] float32 tensor containing the class
          for boxes.
        'nmsed_masks': (optional) a [max_detections, mask_height, mask_width]
          float32 tensor containing masks for each selected box. This is set to
          None if input `masks` is None.
        'nmsed_additional_fields':  (optional) A variable number of float32
          tensors each with size [max_detections, ...] corresponding to the
          input `per_image_additional_fields`.
        'num_detections': A [batch_size] int32 tensor indicating the number of
          valid detections per batch item. Only the top num_detections[i]
          entries in nms_boxes[i], nms_scores[i] and nms_class[i] are valid. The
          rest of the entries are zero paddings.
      """
      per_image_boxes = args[0]
      per_image_scores = args[1]
      per_image_masks = args[2]
      per_image_clip_window = args[3]
      # Make sure that the order of elements passed in args is aligned with
      # the iteration order of ordered_additional_fields
      per_image_additional_fields = {
          key: value
          for key, value in zip(ordered_additional_fields, args[4:-1])
      }
      per_image_num_valid_boxes = args[-1]
      if use_static_shapes:
        total_proposals = tf.shape(per_image_scores)
        per_image_scores = tf.where(
            tf.less(tf.range(total_proposals[0]), per_image_num_valid_boxes),
            per_image_scores,
            tf.fill(total_proposals, np.finfo('float32').min))
      else:
        per_image_boxes = tf.reshape(
            tf.slice(per_image_boxes, 3 * [0],
                     tf.stack([per_image_num_valid_boxes, -1, -1])), [-1, q, 4])
        per_image_scores = tf.reshape(
            tf.slice(per_image_scores, [0, 0],
                     tf.stack([per_image_num_valid_boxes, -1])),
            [-1, num_classes])
        per_image_masks = tf.reshape(
            tf.slice(per_image_masks, 4 * [0],
                     tf.stack([per_image_num_valid_boxes, -1, -1, -1])),
            [-1, q, shape_utils.get_dim_as_int(per_image_masks.shape[2]),
             shape_utils.get_dim_as_int(per_image_masks.shape[3])])
        if per_image_additional_fields is not None:
          for key, tensor in per_image_additional_fields.items():
            additional_field_shape = tensor.get_shape()
            additional_field_dim = len(additional_field_shape)
            per_image_additional_fields[key] = tf.reshape(
                tf.slice(
                    per_image_additional_fields[key],
                    additional_field_dim * [0],
                    tf.stack([per_image_num_valid_boxes] +
                             (additional_field_dim - 1) * [-1])), [-1] + [
                                 shape_utils.get_dim_as_int(dim)
                                 for dim in additional_field_shape[1:]
                             ])
      if use_class_agnostic_nms:
        nmsed_boxlist, num_valid_nms_boxes = class_agnostic_non_max_suppression(
            per_image_boxes,
            per_image_scores,
            score_thresh,
            iou_thresh,
            max_classes_per_detection,
            max_total_size,
            clip_window=per_image_clip_window,
            change_coordinate_frame=change_coordinate_frame,
            masks=per_image_masks,
            pad_to_max_output_size=use_static_shapes,
            use_partitioned_nms=use_partitioned_nms,
            additional_fields=per_image_additional_fields,
            soft_nms_sigma=soft_nms_sigma)
      else:
        nmsed_boxlist, num_valid_nms_boxes = multiclass_non_max_suppression(
            per_image_boxes,
            per_image_scores,
            score_thresh,
            iou_thresh,
            max_size_per_class,
            max_total_size,
            clip_window=per_image_clip_window,
            change_coordinate_frame=change_coordinate_frame,
            masks=per_image_masks,
            pad_to_max_output_size=use_static_shapes,
            use_partitioned_nms=use_partitioned_nms,
            additional_fields=per_image_additional_fields,
            soft_nms_sigma=soft_nms_sigma,
            use_hard_nms=use_hard_nms,
            use_cpu_nms=use_cpu_nms)

      if not use_static_shapes:
        nmsed_boxlist = box_list_ops.pad_or_clip_box_list(
            nmsed_boxlist, max_total_size)
      num_detections = num_valid_nms_boxes
      nmsed_boxes = nmsed_boxlist.get()
      nmsed_scores = nmsed_boxlist.get_field(fields.BoxListFields.scores)
      nmsed_classes = nmsed_boxlist.get_field(fields.BoxListFields.classes)
      nmsed_masks = nmsed_boxlist.get_field(fields.BoxListFields.masks)
      nmsed_additional_fields = []
      # Sorting is needed here to ensure that the values stored in
      # nmsed_additional_fields are always kept in the same order
      # across different execution runs.
      for key in sorted(per_image_additional_fields.keys()):
        nmsed_additional_fields.append(nmsed_boxlist.get_field(key))
      return ([nmsed_boxes, nmsed_scores, nmsed_classes, nmsed_masks] +
              nmsed_additional_fields + [num_detections])