def run_hp_search_optuna(trainer, n_trials: int, direction: str, **kwargs) -> BestRun:
    import optuna
    from accelerate.utils.memory import release_memory

    if trainer.args.process_index == 0:

        def _objective(trial: optuna.Trial, checkpoint_dir=None):
            checkpoint = None
            if checkpoint_dir:
                for subdir in os.listdir(checkpoint_dir):
                    if subdir.startswith(PREFIX_CHECKPOINT_DIR):
                        checkpoint = os.path.join(checkpoint_dir, subdir)
            trainer.objective = None
            if trainer.args.world_size > 1:
                if trainer.args.parallel_mode != ParallelMode.DISTRIBUTED:
                    raise RuntimeError("only support DDP optuna HPO for ParallelMode.DISTRIBUTED currently.")
                trainer.hp_space(trial)
                fixed_trial = optuna.trial.FixedTrial(trial.params, trial.number)
                trial_main_rank_list = [fixed_trial]
                torch.distributed.broadcast_object_list(trial_main_rank_list, src=0)
                trainer.train(resume_from_checkpoint=checkpoint, trial=trial)
            else:
                trainer.train(resume_from_checkpoint=checkpoint, trial=trial)
            # If there hasn't been any evaluation during the training loop.
            if getattr(trainer, "objective", None) is None:
                metrics = trainer.evaluate()
                trainer.objective = trainer.compute_objective(metrics)

            # Free GPU memory
            trainer.model_wrapped, trainer.model = release_memory(trainer.model_wrapped, trainer.model)
            trainer.accelerator.clear()

            return trainer.objective

        timeout = kwargs.pop("timeout", None)
        n_jobs = kwargs.pop("n_jobs", 1)
        gc_after_trial = kwargs.pop("gc_after_trial", False)
        catch = kwargs.pop("catch", ())
        directions = direction if isinstance(direction, list) else None
        direction = None if directions is not None else direction
        study = optuna.create_study(direction=direction, directions=directions, **kwargs)
        study.optimize(
            _objective, n_trials=n_trials, timeout=timeout, n_jobs=n_jobs, gc_after_trial=gc_after_trial, catch=catch
        )
        if not study._is_multi_objective():
            best_trial = study.best_trial
            return BestRun(str(best_trial.number), best_trial.value, best_trial.params)
        else:
            best_trials = study.best_trials
            return [BestRun(str(best.number), best.values, best.params) for best in best_trials]
    else:
        for i in range(n_trials):
            trainer.objective = None
            trial_main_rank_list = [None]
            if trainer.args.parallel_mode != ParallelMode.DISTRIBUTED:
                raise RuntimeError("only support DDP optuna HPO for ParallelMode.DISTRIBUTED currently.")
            torch.distributed.broadcast_object_list(trial_main_rank_list, src=0)
            trainer.train(resume_from_checkpoint=None, trial=trial_main_rank_list[0])
            # If there hasn't been any evaluation during the training loop.
            if getattr(trainer, "objective", None) is None:
                metrics = trainer.evaluate()
                trainer.objective = trainer.compute_objective(metrics)
        return None