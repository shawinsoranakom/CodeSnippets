def aggregate_logs(
      self,
      state: Optional[Any] = None,
      step_outputs: Optional[Dict[str, Any]] = None,
  ) -> Optional[Any]:
    """Optional aggregation over logs returned from a validation step."""
    if not state:
      # The metrics which update state on CPU.
      if self.task_config.use_coco_metrics:
        self.coco_metric.reset_states()
      if self.task_config.use_wod_metrics:
        self.wod_metric.reset_states()

    if self.task_config.use_coco_metrics:
      self.coco_metric.update_state(
          step_outputs[self.coco_metric.name][0],
          step_outputs[self.coco_metric.name][1],
      )
    if self.task_config.use_wod_metrics:
      self.wod_metric.update_state(
          step_outputs[self.wod_metric.name][0],
          step_outputs[self.wod_metric.name][1],
      )

    if 'visualization' in step_outputs:
      # Update detection state for writing summary if there are artifacts for
      # visualization.
      if state is None:
        state = {}
      state.update(visualization_utils.update_detection_state(step_outputs))
      # TODO(allenyan): Mapping `detection_masks` (w.r.t. the `gt_boxes`) back
      # to full masks (w.r.t. the image). Disable mask visualization fow now.
      state.pop('detection_masks', None)

    if not state:
      # Create an arbitrary state to indicate it's not the first step in the
      # following calls to this function.
      state = True
    return state