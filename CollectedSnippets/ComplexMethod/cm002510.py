def push_to_hub(
        self,
        commit_message: str | None = "End of training",
        blocking: bool = True,
        token: str | None = None,
        revision: str | None = None,
        **kwargs,
    ) -> CommitInfo:
        """
        Upload `self.model` and `self.processing_class` to the 🤗 model hub on the repo `self.args.hub_model_id`.

        Parameters:
            commit_message (`str`, *optional*, defaults to `"End of training"`):
                Message to commit while pushing.
            blocking (`bool`, *optional*, defaults to `True`):
                Whether the function should return only when the `git push` has finished.
            token (`str`, *optional*, defaults to `None`):
                Token with write permission to overwrite Trainer's original args.
            revision (`str`, *optional*):
                The git revision to commit from. Defaults to the head of the "main" branch.
            kwargs (`dict[str, Any]`, *optional*):
                Additional keyword arguments passed along to [`~Trainer.create_model_card`].

        Returns:
            The URL of the repository where the model was pushed if `blocking=False`, or a `Future` object tracking the
            progress of the commit if `blocking=True`.
        """
        self.callback_handler.on_push_begin(self.args, self.state, self.control)

        model_name = kwargs.pop("model_name", None)
        if model_name is None and self.args.should_save:
            if self.args.hub_model_id is None:
                model_name = Path(self.args.output_dir).name
            else:
                model_name = self.args.hub_model_id.split("/")[-1]
        token = token if token is not None else self.args.hub_token

        # In case the user calls this method with args.push_to_hub = False
        if self.hub_model_id is None:
            self.init_hf_repo(token=token)

        # Needs to be executed on all processes for TPU training, but will only save on the processed determined by
        # self.args.should_save.
        self.save_model(_internal_call=True)

        # Only push from one node.
        if not self.is_world_process_zero():
            return

        # Add additional tags in the case the model has already some tags and users pass
        # "tags" argument to `push_to_hub` so that trainer automatically handles internal tags
        # from all models since Trainer does not call `model.push_to_hub`.
        if getattr(self.model, "model_tags", None) is not None:
            if "tags" not in kwargs:
                kwargs["tags"] = []

            # If it is a string, convert it to a list
            if isinstance(kwargs["tags"], str):
                kwargs["tags"] = [kwargs["tags"]]

            for model_tag in self.model.model_tags:
                if model_tag not in kwargs["tags"]:
                    kwargs["tags"].append(model_tag)

        self.create_model_card(model_name=model_name, **kwargs)

        if revision is None:
            revision = self.args.hub_revision

        # Wait for the current upload to be finished.
        self._finish_current_push()

        return upload_folder(
            repo_id=self.hub_model_id,
            folder_path=self.args.output_dir,
            commit_message=commit_message,
            token=token,
            run_as_future=not blocking,
            ignore_patterns=["_*", f"{PREFIX_CHECKPOINT_DIR}-*"],
            revision=revision,
        )