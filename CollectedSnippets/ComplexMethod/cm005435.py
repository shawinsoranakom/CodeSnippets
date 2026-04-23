def on_push_begin(self, args, state, control, model, **kwargs):
        if not state.is_world_process_zero or self._trackio is None:
            return
        if (current_project := self._trackio.context_vars.current_project.get()) is None:
            return
        if self._space_id or args.trackio_static_space_id is False:
            # If there's a Gradio space, it will be frozen after training is complete, so we don't need to sync it here.
            # If a user has explicitly set trackio_static_space_id to False, we also don't sync their logs.
            return
        static_space_id = (
            self._static_space_id or args.trackio_static_space_id or self._space_repo_name_from_project(args.project)
        )
        self._static_space_id = self._trackio.sync(
            project=current_project,
            sdk="static",
            space_id=static_space_id,
            private=args.hub_private_repo,
            bucket_id=args.trackio_bucket_id,
            force=True,
        )
        self._point_model_card_at_space(model)