def on_save(self, args, state, control, **kwargs):
        if self._log_model == WandbLogModel.CHECKPOINT and self._initialized and state.is_world_process_zero:
            checkpoint_metadata = {
                k: v
                for k, v in dict(self._wandb.summary).items()
                if isinstance(v, numbers.Number) and not k.startswith("_")
            }
            checkpoint_metadata["model/num_parameters"] = self._wandb.config.get("model/num_parameters")

            ckpt_dir = f"checkpoint-{state.global_step}"
            artifact_path = os.path.join(args.output_dir, ckpt_dir)
            logger.info(f"Logging checkpoint artifacts in {ckpt_dir}. ...")
            checkpoint_name = (
                f"model-{self._wandb.run.id}"
                if (args.run_name is None or args.run_name == args.output_dir)
                else f"model-{self._wandb.run.name}"
            )
            artifact = self._wandb.Artifact(name=checkpoint_name, type="model", metadata=checkpoint_metadata)
            artifact.add_dir(artifact_path)
            self._wandb.log_artifact(
                artifact, aliases=[f"epoch_{round(state.epoch, 2)}", f"checkpoint_global_step_{state.global_step}"]
            )