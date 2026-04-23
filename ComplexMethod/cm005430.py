def on_train_end(self, args: TrainingArguments, state, control, model=None, processing_class=None, **kwargs):
        if self._wandb is None:
            return
        if self._log_model.is_enabled and self._initialized and state.is_world_process_zero:
            from ..trainer import Trainer

            args_for_fake = copy.deepcopy(args)
            args_for_fake.deepspeed = None
            args_for_fake.deepspeed_plugin = None
            fake_trainer = Trainer(
                args=args_for_fake, model=model, processing_class=processing_class, eval_dataset=["fake"]
            )
            with tempfile.TemporaryDirectory() as temp_dir:
                fake_trainer.save_model(temp_dir)
                metadata = (
                    {
                        k: v
                        for k, v in dict(self._wandb.summary).items()
                        if isinstance(v, numbers.Number) and not k.startswith("_")
                    }
                    if not args.load_best_model_at_end
                    else {
                        f"eval/{args.metric_for_best_model}": state.best_metric,
                        "train/total_floss": state.total_flos,
                        "model/num_parameters": self._wandb.config.get("model/num_parameters"),
                    }
                )
                metadata["final_model"] = True
                logger.info("Logging model artifacts. ...")
                model_name = (
                    f"model-{self._wandb.run.id}"
                    if (args.run_name is None or args.run_name == args.output_dir)
                    else f"model-{self._wandb.run.name}"
                )
                # add the model architecture to a separate text file
                save_model_architecture_to_file(model, temp_dir)

                artifact = self._wandb.Artifact(name=model_name, type="model", metadata=metadata)
                for f in Path(temp_dir).glob("*"):
                    if f.is_file():
                        with artifact.new_file(f.name, mode="wb") as fa:
                            fa.write(f.read_bytes())
                self._wandb.run.log_artifact(artifact, aliases=["final_model"])