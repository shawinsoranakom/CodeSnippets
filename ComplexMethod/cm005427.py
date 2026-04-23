def _objective():
        run = wandb.run if wandb.run else wandb.init()
        trainer.state.trial_name = run.name
        run.config.update({"assignments": {}, "metric": metric})
        config = wandb.config

        trainer.objective = None

        trainer.train(resume_from_checkpoint=None, trial=vars(config)["_items"])
        # If there hasn't been any evaluation during the training loop.
        if getattr(trainer, "objective", None) is None:
            metrics = trainer.evaluate()
            trainer.objective = trainer.compute_objective(metrics)
            format_metrics = rewrite_logs(metrics)
            if metric not in format_metrics:
                logger.warning(
                    f"Provided metric {metric} not found. This might result in unexpected sweeps charts. The available"
                    f" metrics are {format_metrics.keys()}"
                )
        best_score = False
        if best_trial["run_id"] is not None:
            if direction == "minimize":
                best_score = trainer.objective < best_trial["objective"]
            elif direction == "maximize":
                best_score = trainer.objective > best_trial["objective"]

        if best_score or best_trial["run_id"] is None:
            best_trial["run_id"] = run.id
            best_trial["objective"] = trainer.objective
            best_trial["hyperparameters"] = dict(config)

        return trainer.objective