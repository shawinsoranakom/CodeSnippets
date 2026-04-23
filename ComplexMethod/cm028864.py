def aggregate_logs(self, state=None, step_outputs=None):
    if self._task_config.use_coco_metrics:
      if state is None:
        self.coco_metric.reset_states()
      self.coco_metric.update_state(step_outputs[self.coco_metric.name][0],
                                    step_outputs[self.coco_metric.name][1])
    if self._task_config.use_wod_metrics:
      if state is None:
        self.wod_metric.reset_states()
      self.wod_metric.update_state(step_outputs[self.wod_metric.name][0],
                                   step_outputs[self.wod_metric.name][1])

    if 'visualization' in step_outputs:
      # Update detection state for writing summary if there are artifacts for
      # visualization.
      if state is None:
        state = {}
      state.update(visualization_utils.update_detection_state(step_outputs))

    if state is None:
      # Create an arbitrary state to indicate it's not the first step in the
      # following calls to this function.
      state = True

    return state