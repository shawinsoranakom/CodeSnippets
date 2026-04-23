def _build_controller(
      self,
      trainer,
      evaluator,
      save_summary: bool = True,
      train_actions: Optional[List[orbit.Action]] = None,
      eval_actions: Optional[List[orbit.Action]] = None,
      controller_cls=orbit.Controller,
      enable_async_checkpointing: bool = False,
  ) -> orbit.Controller:
    """Builds a Orbit controler."""
    train_actions = [] if not train_actions else train_actions
    if trainer:
      checkpoint_manager = self.checkpoint_manager
      assert checkpoint_manager, 'Checkpoint manager required but undefined.'
      train_actions += actions.get_train_actions(
          self.params,
          trainer,
          self.model_dir,
          checkpoint_manager=checkpoint_manager,
      )

    eval_actions = [] if not eval_actions else eval_actions
    if evaluator:
      eval_actions += actions.get_eval_actions(self.params, evaluator,
                                               self.model_dir)

    if save_summary:
      eval_summary_dir = os.path.join(
          self.model_dir, self.params.trainer.validation_summary_subdir
      )
    else:
      eval_summary_dir = None

    controller = controller_cls(
        strategy=self.strategy,
        trainer=trainer,
        evaluator=evaluator,
        global_step=self.trainer.global_step,
        steps_per_loop=self.params.trainer.steps_per_loop,
        checkpoint_manager=self.checkpoint_manager,
        enable_async_checkpointing=enable_async_checkpointing,
        summary_dir=os.path.join(self.model_dir, 'train')
        if (save_summary)
        else None,
        eval_summary_dir=eval_summary_dir,
        summary_interval=self.params.trainer.summary_interval
        if (save_summary)
        else None,
        train_actions=train_actions,
        eval_actions=eval_actions,
        summary_manager=self._summary_manager
        if hasattr(self, '_summary_manager')
        else None,
        eval_summary_manager=self._eval_summary_manager
        if hasattr(self, '_eval_summary_manager')
        else None,
    )
    return controller