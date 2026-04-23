def _push_from_checkpoint(self, checkpoint_folder: str) -> None:
        """Push model and checkpoint files to the Hub from a checkpoint folder."""
        if not self.is_world_process_zero() or self.args.hub_strategy == HubStrategy.END:
            return
        # If we haven't finished the last push, we don't do this one unless args.hub_always_push=True.
        if not self.args.hub_always_push and self.push_in_progress is not None and not self.push_in_progress.is_done():
            return

        self.callback_handler.on_push_begin(self.args, self.state, self.control)
        output_dir = self.args.output_dir
        # To avoid a new synchronization of all model weights, we just copy the file from the checkpoint folder
        modeling_files = [CONFIG_NAME, GENERATION_CONFIG_NAME, WEIGHTS_NAME, SAFE_WEIGHTS_NAME]
        #  Add sharded checkpoints if we have an index
        for index_file in [WEIGHTS_INDEX_NAME, SAFE_WEIGHTS_INDEX_NAME]:
            index_path = os.path.join(checkpoint_folder, index_file)
            if os.path.isfile(index_path):
                modeling_files.append(index_file)
                with open(index_path) as f:
                    index = json.loads(f.read())
                shard_files = list(set(index["weight_map"].values()))
                modeling_files.extend(shard_files)
        if is_peft_available():
            modeling_files.extend([ADAPTER_CONFIG_NAME, ADAPTER_WEIGHTS_NAME, ADAPTER_SAFE_WEIGHTS_NAME])
        for modeling_file in modeling_files:
            if os.path.isfile(os.path.join(checkpoint_folder, modeling_file)):
                shutil.copy(os.path.join(checkpoint_folder, modeling_file), os.path.join(output_dir, modeling_file))
        # Saving the processing class is fast and we don't know how many files it may have spawned, so we resave it to be sure.
        if self.processing_class is not None:
            self.processing_class.save_pretrained(output_dir)
        # Same for the training arguments
        torch.save(self.args, os.path.join(output_dir, TRAINING_ARGS_NAME))

        if self.args.save_strategy == SaveStrategy.STEPS:
            commit_message = f"Training in progress, step {self.state.global_step}"
        else:
            commit_message = f"Training in progress, epoch {int(self.state.epoch)}"

        model_push_job = upload_folder(
            repo_id=self.hub_model_id,
            folder_path=output_dir,
            commit_message=commit_message,
            token=self.args.hub_token,
            run_as_future=True,
            ignore_patterns=["_*", f"{PREFIX_CHECKPOINT_DIR}-*"],
            revision=self.args.hub_revision,
        )

        push_jobs = [model_push_job]

        if self.args.hub_strategy in [HubStrategy.CHECKPOINT, HubStrategy.ALL_CHECKPOINTS]:
            path_in_repo = (
                "last-checkpoint" if self.args.hub_strategy == HubStrategy.CHECKPOINT else Path(checkpoint_folder).name
            )
            checkpoint_push = upload_folder(
                repo_id=self.hub_model_id,
                folder_path=checkpoint_folder,
                path_in_repo=path_in_repo,
                commit_message=commit_message + ", checkpoint",
                token=self.args.hub_token,
                run_as_future=True,
                revision=self.args.hub_revision,
            )
            push_jobs.append(checkpoint_push)

        if self.push_in_progress is None or self.push_in_progress.is_done():
            self.push_in_progress = PushInProgress(push_jobs)
        else:
            self.push_in_progress.jobs.extend(push_jobs)