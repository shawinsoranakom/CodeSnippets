def _build_frcnn_losses(
      self,
      outputs: Mapping[str, Any],
      labels: Mapping[str, Any],
  ) -> Tuple[tf.Tensor, tf.Tensor]:
    """Builds losses for Fast R-CNN."""
    cascade_ious = self.task_config.model.roi_sampler.cascade_iou_thresholds

    frcnn_cls_loss_fn = maskrcnn_losses.FastrcnnClassLoss(
        use_binary_cross_entropy=self.task_config.losses
        .frcnn_class_use_binary_cross_entropy,
        top_k_percent=self.task_config.losses.frcnn_class_loss_top_k_percent)
    frcnn_box_loss_fn = maskrcnn_losses.FastrcnnBoxLoss(
        self.task_config.losses.frcnn_huber_loss_delta,
        self.task_config.model.detection_head.class_agnostic_bbox_pred)

    # Final cls/box losses are computed as an average of all detection heads.
    frcnn_cls_loss = 0.0
    frcnn_box_loss = 0.0
    num_det_heads = 1 if cascade_ious is None else 1 + len(cascade_ious)
    for cas_num in range(num_det_heads):
      frcnn_cls_loss_i = tf.reduce_mean(
          frcnn_cls_loss_fn(
              outputs[
                  'class_outputs_{}'.format(cas_num)
                  if cas_num
                  else 'class_outputs'
              ],
              outputs[
                  'class_targets_{}'.format(cas_num)
                  if cas_num
                  else 'class_targets'
              ],
              self.task_config.losses.class_weights,
          )
      )
      frcnn_box_loss_i = tf.reduce_mean(
          frcnn_box_loss_fn(
              outputs['box_outputs_{}'.format(cas_num
                                             ) if cas_num else 'box_outputs'],
              outputs['class_targets_{}'
                      .format(cas_num) if cas_num else 'class_targets'],
              outputs['box_targets_{}'.format(cas_num
                                             ) if cas_num else 'box_targets']))
      frcnn_cls_loss += frcnn_cls_loss_i
      frcnn_box_loss += frcnn_box_loss_i
    frcnn_cls_loss /= num_det_heads
    frcnn_box_loss /= num_det_heads
    return frcnn_cls_loss, frcnn_box_loss