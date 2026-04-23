def call(self, labels, predictions):
    labels = merge_labels(labels)
    p = {}
    for key in predictions:
      # [batch_size, num_anchors, height, width, num_classes + boxes + obj]
      p[key] = tf.transpose(predictions[key], [0, 3, 1, 2, 4])
    cls_loss, box_loss, obj_loss, iou_metric = [tf.zeros(1) for _ in range(4)]
    total_num_matchings = tf.zeros(1)
    total_num_gts = tf.reduce_sum(tf.cast(labels[..., 0] != -1, tf.float32))

    masks, indices, anchors, cls_targets, box_targets = self._build_targets(
        labels, p)

    batch_size = tf.shape(indices)[0]
    layer_shape = [batch_size, self._num_layers, -1]
    # [anchor_indices, grid_js, grid_is]
    masks = tf.reshape(masks, layer_shape)
    indices = tf.reshape(indices, [*layer_shape, 3])
    anchors = tf.reshape(anchors, [*layer_shape, 2])
    cls_targets = tf.reshape(cls_targets, layer_shape)
    box_targets = tf.reshape(box_targets, [*layer_shape, 4])

    # Losses
    for layer_key, layer_pred in p.items():
      i = int(layer_key) - 3

      obj_targets = tf.zeros_like(layer_pred[..., 0])

      layer_masks = masks[:, i]
      num_matchings = tf.reduce_sum(tf.cast(layer_masks, tf.int32))
      total_num_matchings += tf.cast(num_matchings, tf.float32)

      if num_matchings > 0:
        layer_indices = indices[:, i]
        batch_indices = tf.tile(
            tf.range(batch_size)[:, None], [1, tf.shape(layer_indices)[1]]
        )[..., None]
        layer_indices = tf.concat([batch_indices, layer_indices], axis=-1)
        layer_indices = tf.boolean_mask(layer_indices, layer_masks)
        layer_anchors = tf.boolean_mask(anchors[:, i], layer_masks)

        layer_cls_targets = tf.boolean_mask(cls_targets[:, i], layer_masks)
        layer_box_targets = tf.boolean_mask(box_targets[:, i], layer_masks)

        # In the same shape of layer_target.
        matched_pred = tf.gather_nd(layer_pred, layer_indices)

        pred_xcyc = tf.sigmoid(matched_pred[..., :2]) * 2 - 0.5
        pred_wh = (
            tf.square(tf.sigmoid(matched_pred[..., 2:4]) * 2) * layer_anchors)
        pred_xcycwh = tf.concat([pred_xcyc, pred_wh], axis=-1)
        _, ciou = box_ops.compute_ciou(pred_xcycwh, layer_box_targets)

        box_loss += tf.reduce_mean(1.0 - ciou)
        iou_metric += tf.reduce_mean(ciou)

        # Compute classification loss.
        if self._num_classes > 1:  # cls loss (only if multiple classes)
          t = tf.one_hot(
              layer_cls_targets,
              self._num_classes,
              on_value=self._pos_targets,
              off_value=self._neg_targets,
          )
          cls_loss += tf.reduce_mean(
              self._cls_loss_fn(t, matched_pred[..., 5:]))

        # Compute objectness loss.
        iou_ratio = tf.cast(
            (1.0 - self._iou_mix_ratio)
            + (self._iou_mix_ratio * tf.maximum(tf.stop_gradient(ciou), 0)),
            obj_targets.dtype,
        )
        obj_targets = tf.tensor_scatter_nd_max(
            obj_targets, layer_indices, iou_ratio
        )
      layer_obj_loss = tf.reduce_mean(
          self._obj_loss_fn(obj_targets, layer_pred[..., 4])
      )
      obj_loss += layer_obj_loss * self._balance[i]
      # Updates the balance factor, which is a moving average of previous
      # factor at the same level.
      if self._auto_balance:
        self._balance[i] = self._balance[
            i
        ] * 0.9999 + 0.0001 / tf.stop_gradient(layer_obj_loss)

    # Re-balance the factors so that stride at self._ssi always receives 1.
    if self._auto_balance:
      self._balance = [x / self._balance[self._ssi] for x in self._balance]

    box_loss *= self._box_weight
    obj_loss *= self._obj_weight
    cls_loss *= self._cls_weight

    self._box_loss = tf.stop_gradient(box_loss)
    self._obj_loss = tf.stop_gradient(obj_loss)
    self._cls_loss = tf.stop_gradient(cls_loss)
    self._iou = tf.stop_gradient(iou_metric) / self._num_layers
    self._num_matchings = tf.stop_gradient(
        total_num_matchings) / tf.cast(batch_size, tf.float32)
    self._num_gts = tf.stop_gradient(
        total_num_gts) / tf.cast(batch_size, tf.float32)

    loss = box_loss + obj_loss + cls_loss
    return loss * tf.cast(batch_size, loss.dtype)