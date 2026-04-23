def run_hp_search_ray(trainer, n_trials: int, direction: str, **kwargs) -> BestRun:
    """
    Environment:
        - **RAY_SCOPE** (`str`, *optional*, defaults to `"last"`):
            The scope to use when doing hyperparameter search with Ray. By default, `"last"` will be used. Ray
            will then use the last checkpoint of all trials, compare those, and select the best one. However,
            other options are also available. See the Ray documentation (https://docs.ray.io/en/latest/tune/api_docs/analysis.html#ray.tune.ExperimentAnalysis.get_best_trial)
            for more options
    """
    import ray.tune

    def _objective(trial: dict, local_trainer):
        try:
            from transformers.utils.notebook import NotebookProgressCallback

            if local_trainer.pop_callback(NotebookProgressCallback):
                local_trainer.add_callback(ProgressCallback)
        except ModuleNotFoundError:
            pass

        local_trainer.objective = None

        checkpoint = ray.tune.get_checkpoint()
        if checkpoint:
            # Upon trial resume, the local_trainer's objective gets reset to None.
            # If `local_trainer.train` is a noop (training has already reached
            # the target number of epochs/steps), then this would
            # trigger an unnecessary extra checkpoint at the end of training.
            # -> Set the objective to a dummy value upon resume as a workaround.
            local_trainer.objective = "objective"

            with checkpoint.as_directory() as checkpoint_dir:
                checkpoint_path = next(Path(checkpoint_dir).glob(f"{PREFIX_CHECKPOINT_DIR}*")).as_posix()
                local_trainer.train(resume_from_checkpoint=checkpoint_path, trial=trial)
        else:
            local_trainer.train(trial=trial)

        # If there hasn't been any evaluation during the training loop.
        if getattr(local_trainer, "objective", None) is None:
            metrics = local_trainer.evaluate()
            local_trainer.objective = local_trainer.compute_objective(metrics)

            metrics.update({"objective": local_trainer.objective, "done": True})

            with tempfile.TemporaryDirectory() as temp_checkpoint_dir:
                local_trainer._tune_save_checkpoint(checkpoint_dir=temp_checkpoint_dir)
                checkpoint = ray.tune.Checkpoint.from_directory(temp_checkpoint_dir)
                ray.tune.report(metrics, checkpoint=checkpoint)

    if not trainer._memory_tracker.skip_memory_metrics:
        from ..trainer_utils import TrainerMemoryTracker

        logger.warning(
            "Memory tracking for your Trainer is currently "
            "enabled. Automatically disabling the memory tracker "
            "since the memory tracker is not serializable."
        )
        trainer._memory_tracker = TrainerMemoryTracker(skip_memory_metrics=True)

    # The model and TensorBoard writer do not pickle so we have to remove them (if they exists)
    # while doing the ray hp search.
    _tb_writer = trainer.pop_callback(TensorBoardCallback)
    trainer.model = None

    # Setup default `resources_per_trial`.
    if "resources_per_trial" not in kwargs:
        # Default to 1 CPU and 1 GPU (if applicable) per trial.
        kwargs["resources_per_trial"] = {"cpu": 1}
        if trainer.args.n_gpu > 0:
            kwargs["resources_per_trial"]["gpu"] = 1
        resource_msg = "1 CPU" + (" and 1 GPU" if trainer.args.n_gpu > 0 else "")
        logger.info(
            "No `resources_per_trial` arg was passed into "
            "`hyperparameter_search`. Setting it to a default value "
            f"of {resource_msg} for each trial."
        )
    # Make sure each trainer only uses GPUs that were allocated per trial.
    gpus_per_trial = kwargs["resources_per_trial"].get("gpu", 0)
    trainer.args._n_gpu = gpus_per_trial

    # Setup default `progress_reporter`.
    if "progress_reporter" not in kwargs:
        from ray.tune import CLIReporter

        kwargs["progress_reporter"] = CLIReporter(metric_columns=["objective"])

    if "scheduler" in kwargs:
        from ray.tune.schedulers import ASHAScheduler, HyperBandForBOHB, MedianStoppingRule, PopulationBasedTraining

        # Check for `do_eval` and `eval_during_training` for schedulers that require intermediate reporting.
        if isinstance(
            kwargs["scheduler"], (ASHAScheduler, MedianStoppingRule, HyperBandForBOHB, PopulationBasedTraining)
        ) and (not trainer.args.do_eval or trainer.args.eval_strategy == IntervalStrategy.NO):
            raise RuntimeError(
                "You are using {cls} as a scheduler but you haven't enabled evaluation during training. "
                "This means your trials will not report intermediate results to Ray Tune, and "
                "can thus not be stopped early or used to exploit other trials parameters. "
                "If this is what you want, do not use {cls}. If you would like to use {cls}, "
                "make sure you pass `do_eval=True` and `eval_strategy='steps'` in the "
                "Trainer `args`.".format(cls=type(kwargs["scheduler"]).__name__)
            )

    trainable = ray.tune.with_parameters(_objective, local_trainer=trainer)

    @functools.wraps(trainable)
    def dynamic_modules_import_trainable(*args, **kwargs):
        """
        Wrapper around `tune.with_parameters` to ensure datasets_modules are loaded on each Actor.

        Without this, an ImportError will be thrown. See https://github.com/huggingface/transformers/issues/11565.

        Assumes that `_objective`, defined above, is a function.
        """
        if is_datasets_available() and packaging.version.parse(
            importlib.metadata.version("datasets")
        ) < packaging.version.parse("4.0.0"):
            import datasets.load

            dynamic_modules_path = os.path.join(datasets.load.init_dynamic_modules(), "__init__.py")
            # load dynamic_modules from path
            spec = importlib.util.spec_from_file_location("datasets_modules", dynamic_modules_path)
            datasets_modules = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = datasets_modules
            spec.loader.exec_module(datasets_modules)
        return trainable(*args, **kwargs)

    # special attr set by tune.with_parameters
    if hasattr(trainable, "__mixins__"):
        dynamic_modules_import_trainable.__mixins__ = trainable.__mixins__

    analysis = ray.tune.run(
        dynamic_modules_import_trainable,
        config=trainer.hp_space(None),
        num_samples=n_trials,
        **kwargs,
    )
    ray_scope = os.getenv("RAY_SCOPE", "last")
    best_trial = analysis.get_best_trial(metric="objective", mode=direction[:3], scope=ray_scope)
    best_run = BestRun(best_trial.trial_id, best_trial.last_result["objective"], best_trial.config, analysis)
    if _tb_writer is not None:
        trainer.add_callback(_tb_writer)
    return best_run