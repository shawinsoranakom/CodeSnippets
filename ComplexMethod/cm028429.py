def _maybe_export_non_progressive_checkpoint(self, export_ckpt_dir):
    """Export checkpoints in non-progressive format.

    This basically removes the wrapping of self._task.cur_checkpoint_items
    -- just save the model, optimizer, etc., directly.
    The purpose is to let your down-stream tasks to use these checkpoints.

    Args:
      export_ckpt_dir: A str. folder of exported checkpoints.
    """
    if not self.config.trainer.export_checkpoint:
      logging.info('Not exporting checkpoints.')
      return
    if not self._task.is_last_stage and (
        self.config.trainer.export_only_final_stage_ckpt):
      logging.info('Not exporting checkpoints until the last stage.')
      return

    if self._export_ckpt_manager is None:
      # Create a checkpoint object just now, to make sure we use
      # progressive_policy.cur_model and progressive_policy.cur_optimizer of the
      # current stage.
      if hasattr(self.model, 'checkpoint_items'):
        checkpoint_items = self.model.checkpoint_items
      else:
        checkpoint_items = {}
      checkpoint = tf.train.Checkpoint(
          global_step=self.global_step,
          model=self.model,
          optimizer=self.optimizer,
          **checkpoint_items)

      max_to_keep = self.config.trainer.export_max_to_keep or (
          self.config.trainer.max_to_keep)
      checkpoint_interval = self.config.trainer.export_checkpoint_interval or (
          self.config.trainer.checkpoint_interval)
      self._export_ckpt_manager = tf.train.CheckpointManager(
          checkpoint,
          directory=export_ckpt_dir,
          checkpoint_name='ckpt',
          step_counter=self.global_step,
          max_to_keep=max_to_keep,
          checkpoint_interval=checkpoint_interval,
      )

    # Make sure we export the last checkpoint.
    last_checkpoint = (
        self.global_step.numpy() == self._config.trainer.train_steps)
    checkpoint_path = self._export_ckpt_manager.save(
        checkpoint_number=self.global_step.numpy(),
        check_interval=not last_checkpoint)
    if checkpoint_path:
      logging.info('Checkpoints exported: %s.', checkpoint_path)