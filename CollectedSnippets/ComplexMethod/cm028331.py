def _loss_box_classifier(self,
                           refined_box_encodings,
                           class_predictions_with_background,
                           proposal_boxes,
                           num_proposals,
                           groundtruth_boxlists,
                           groundtruth_classes_with_background_list,
                           groundtruth_weights_list,
                           image_shape,
                           prediction_masks=None,
                           groundtruth_masks_list=None,
                           detection_boxes=None,
                           num_detections=None):
    """Computes scalar box classifier loss tensors.

    Uses self._detector_target_assigner to obtain regression and classification
    targets for the second stage box classifier, optionally performs
    hard mining, and returns losses.  All losses are computed independently
    for each image and then averaged across the batch.
    Please note that for boxes and masks with multiple labels, the box
    regression and mask prediction losses are only computed for one label.

    This function assumes that the proposal boxes in the "padded" regions are
    actually zero (and thus should not be matched to).


    Args:
      refined_box_encodings: a 3-D tensor with shape
        [total_num_proposals, num_classes, box_coder.code_size] representing
        predicted (final) refined box encodings. If using a shared box across
        classes this will instead have shape
        [total_num_proposals, 1, box_coder.code_size].
      class_predictions_with_background: a 2-D tensor with shape
        [total_num_proposals, num_classes + 1] containing class
        predictions (logits) for each of the anchors.  Note that this tensor
        *includes* background class predictions (at class index 0).
      proposal_boxes: [batch_size, self.max_num_proposals, 4] representing
        decoded proposal bounding boxes.
      num_proposals: A Tensor of type `int32`. A 1-D tensor of shape [batch]
        representing the number of proposals predicted for each image in
        the batch.
      groundtruth_boxlists: a list of BoxLists containing coordinates of the
        groundtruth boxes.
      groundtruth_classes_with_background_list: a list of 2-D one-hot
        (or k-hot) tensors of shape [num_boxes, num_classes + 1] containing the
        class targets with the 0th index assumed to map to the background class.
      groundtruth_weights_list: A list of 1-D tf.float32 tensors of shape
        [num_boxes] containing weights for groundtruth boxes.
      image_shape: a 1-D tensor of shape [4] representing the image shape.
      prediction_masks: an optional 4-D tensor with shape [total_num_proposals,
        num_classes, mask_height, mask_width] containing the instance masks for
        each box.
      groundtruth_masks_list: an optional list of 3-D tensors of shape
        [num_boxes, image_height, image_width] containing the instance masks for
        each of the boxes.
      detection_boxes: 3-D float tensor of shape [batch,
        max_total_detections, 4] containing post-processed detection boxes in
        normalized co-ordinates.
      num_detections: 1-D int32 tensor of shape [batch] containing number of
        valid detections in `detection_boxes`.

    Returns:
      a dictionary mapping loss keys ('second_stage_localization_loss',
        'second_stage_classification_loss') to scalar tensors representing
        corresponding loss values.

    Raises:
      ValueError: if `predict_instance_masks` in
        second_stage_mask_rcnn_box_predictor is True and
        `groundtruth_masks_list` is not provided.
    """
    with tf.name_scope('BoxClassifierLoss'):
      paddings_indicator = self._padded_batched_proposals_indicator(
          num_proposals, proposal_boxes.shape[1])
      proposal_boxlists = [
          box_list.BoxList(proposal_boxes_single_image)
          for proposal_boxes_single_image in tf.unstack(proposal_boxes)]
      batch_size = len(proposal_boxlists)

      num_proposals_or_one = tf.cast(tf.expand_dims(
          tf.maximum(num_proposals, tf.ones_like(num_proposals)), 1),
                                     dtype=tf.float32)
      normalizer = tf.tile(num_proposals_or_one,
                           [1, self.max_num_proposals]) * batch_size

      (batch_cls_targets_with_background, batch_cls_weights, batch_reg_targets,
       batch_reg_weights, _) = target_assigner.batch_assign_targets(
           target_assigner=self._detector_target_assigner,
           anchors_batch=proposal_boxlists,
           gt_box_batch=groundtruth_boxlists,
           gt_class_targets_batch=groundtruth_classes_with_background_list,
           unmatched_class_label=tf.constant(
               [1] + self._num_classes * [0], dtype=tf.float32),
           gt_weights_batch=groundtruth_weights_list)
      if self.groundtruth_has_field(
          fields.InputDataFields.groundtruth_labeled_classes):
        gt_labeled_classes = self.groundtruth_lists(
            fields.InputDataFields.groundtruth_labeled_classes)
        gt_labeled_classes = tf.pad(
            gt_labeled_classes, [[0, 0], [1, 0]],
            mode='CONSTANT',
            constant_values=1)
        batch_cls_weights *= tf.expand_dims(gt_labeled_classes, 1)
      class_predictions_with_background = tf.reshape(
          class_predictions_with_background,
          [batch_size, self.max_num_proposals, -1])

      flat_cls_targets_with_background = tf.reshape(
          batch_cls_targets_with_background,
          [batch_size * self.max_num_proposals, -1])
      one_hot_flat_cls_targets_with_background = tf.argmax(
          flat_cls_targets_with_background, axis=1)
      one_hot_flat_cls_targets_with_background = tf.one_hot(
          one_hot_flat_cls_targets_with_background,
          flat_cls_targets_with_background.get_shape()[1])

      # If using a shared box across classes use directly
      if refined_box_encodings.shape[1] == 1:
        reshaped_refined_box_encodings = tf.reshape(
            refined_box_encodings,
            [batch_size, self.max_num_proposals, self._box_coder.code_size])
      # For anchors with multiple labels, picks refined_location_encodings
      # for just one class to avoid over-counting for regression loss and
      # (optionally) mask loss.
      else:
        reshaped_refined_box_encodings = (
            self._get_refined_encodings_for_postitive_class(
                refined_box_encodings,
                one_hot_flat_cls_targets_with_background, batch_size))

      losses_mask = None
      if self.groundtruth_has_field(fields.InputDataFields.is_annotated):
        losses_mask = tf.stack(self.groundtruth_lists(
            fields.InputDataFields.is_annotated))
      second_stage_loc_losses = self._second_stage_localization_loss(
          reshaped_refined_box_encodings,
          batch_reg_targets,
          weights=batch_reg_weights,
          losses_mask=losses_mask) / normalizer
      second_stage_cls_losses = ops.reduce_sum_trailing_dimensions(
          self._second_stage_classification_loss(
              class_predictions_with_background,
              batch_cls_targets_with_background,
              weights=batch_cls_weights,
              losses_mask=losses_mask),
          ndims=2) / normalizer

      second_stage_loc_loss = tf.reduce_sum(
          second_stage_loc_losses * tf.cast(paddings_indicator,
                                            dtype=tf.float32))
      second_stage_cls_loss = tf.reduce_sum(
          second_stage_cls_losses * tf.cast(paddings_indicator,
                                            dtype=tf.float32))

      if self._hard_example_miner:
        (second_stage_loc_loss, second_stage_cls_loss
        ) = self._unpad_proposals_and_apply_hard_mining(
            proposal_boxlists, second_stage_loc_losses,
            second_stage_cls_losses, num_proposals)
      localization_loss = tf.multiply(self._second_stage_loc_loss_weight,
                                      second_stage_loc_loss,
                                      name='localization_loss')

      classification_loss = tf.multiply(self._second_stage_cls_loss_weight,
                                        second_stage_cls_loss,
                                        name='classification_loss')

      loss_dict = {'Loss/BoxClassifierLoss/localization_loss':
                       localization_loss,
                   'Loss/BoxClassifierLoss/classification_loss':
                       classification_loss}
      second_stage_mask_loss = None
      if prediction_masks is not None:
        if groundtruth_masks_list is None:
          raise ValueError('Groundtruth instance masks not provided. '
                           'Please configure input reader.')

        if not self._is_training:
          (proposal_boxes, proposal_boxlists, paddings_indicator,
           one_hot_flat_cls_targets_with_background
          ) = self._get_mask_proposal_boxes_and_classes(
              detection_boxes, num_detections, image_shape,
              groundtruth_boxlists, groundtruth_classes_with_background_list,
              groundtruth_weights_list)
        unmatched_mask_label = tf.zeros(image_shape[1:3], dtype=tf.float32)
        (batch_mask_targets, _, _, batch_mask_target_weights,
         _) = target_assigner.batch_assign_targets(
             target_assigner=self._detector_target_assigner,
             anchors_batch=proposal_boxlists,
             gt_box_batch=groundtruth_boxlists,
             gt_class_targets_batch=groundtruth_masks_list,
             unmatched_class_label=unmatched_mask_label,
             gt_weights_batch=groundtruth_weights_list)

        # Pad the prediction_masks with to add zeros for background class to be
        # consistent with class predictions.
        if prediction_masks.get_shape().as_list()[1] == 1:
          # Class agnostic masks or masks for one-class prediction. Logic for
          # both cases is the same since background predictions are ignored
          # through the batch_mask_target_weights.
          prediction_masks_masked_by_class_targets = prediction_masks
        else:
          prediction_masks_with_background = tf.pad(
              prediction_masks, [[0, 0], [1, 0], [0, 0], [0, 0]])
          prediction_masks_masked_by_class_targets = tf.boolean_mask(
              prediction_masks_with_background,
              tf.greater(one_hot_flat_cls_targets_with_background, 0))

        mask_height = shape_utils.get_dim_as_int(prediction_masks.shape[2])
        mask_width = shape_utils.get_dim_as_int(prediction_masks.shape[3])
        reshaped_prediction_masks = tf.reshape(
            prediction_masks_masked_by_class_targets,
            [batch_size, -1, mask_height * mask_width])

        batch_mask_targets_shape = tf.shape(batch_mask_targets)
        flat_gt_masks = tf.reshape(batch_mask_targets,
                                   [-1, batch_mask_targets_shape[2],
                                    batch_mask_targets_shape[3]])

        # Use normalized proposals to crop mask targets from image masks.
        flat_normalized_proposals = box_list_ops.to_normalized_coordinates(
            box_list.BoxList(tf.reshape(proposal_boxes, [-1, 4])),
            image_shape[1], image_shape[2], check_range=False).get()

        flat_cropped_gt_mask = self._crop_and_resize_fn(
            [tf.expand_dims(flat_gt_masks, -1)],
            tf.expand_dims(flat_normalized_proposals, axis=1), None,
            [mask_height, mask_width])
        # Without stopping gradients into cropped groundtruth masks the
        # performance with 100-padded groundtruth masks when batch size > 1 is
        # about 4% worse.
        # TODO(rathodv): Investigate this since we don't expect any variables
        # upstream of flat_cropped_gt_mask.
        flat_cropped_gt_mask = tf.stop_gradient(flat_cropped_gt_mask)

        batch_cropped_gt_mask = tf.reshape(
            flat_cropped_gt_mask,
            [batch_size, -1, mask_height * mask_width])

        mask_losses_weights = (
            batch_mask_target_weights * tf.cast(paddings_indicator,
                                                dtype=tf.float32))
        mask_losses = self._second_stage_mask_loss(
            reshaped_prediction_masks,
            batch_cropped_gt_mask,
            weights=tf.expand_dims(mask_losses_weights, axis=-1),
            losses_mask=losses_mask)
        total_mask_loss = tf.reduce_sum(mask_losses)
        normalizer = tf.maximum(
            tf.reduce_sum(mask_losses_weights * mask_height * mask_width), 1.0)
        second_stage_mask_loss = total_mask_loss / normalizer

      if second_stage_mask_loss is not None:
        mask_loss = tf.multiply(self._second_stage_mask_loss_weight,
                                second_stage_mask_loss, name='mask_loss')
        loss_dict['Loss/BoxClassifierLoss/mask_loss'] = mask_loss
    return loss_dict