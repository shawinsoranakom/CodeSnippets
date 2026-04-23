def _get_expected_events(self, trainer):
        """Compute the exact expected event sequence for a training run."""
        expected_events = ["on_init_end", "on_train_begin"]
        step = 0
        train_dl_len = len(trainer.get_eval_dataloader())
        evaluation_events = ["on_prediction_step"] * len(trainer.get_eval_dataloader()) + ["on_log", "on_evaluate"]
        for _ in range(trainer.state.num_train_epochs):
            expected_events.append("on_epoch_begin")
            for _ in range(train_dl_len):
                step += 1
                expected_events += ["on_step_begin", "on_pre_optimizer_step", "on_optimizer_step", "on_step_end"]
                if step % trainer.args.logging_steps == 0:
                    expected_events.append("on_log")
                if trainer.args.eval_strategy == IntervalStrategy.STEPS and step % trainer.args.eval_steps == 0:
                    expected_events += evaluation_events.copy()
                # End-of-training evaluation: triggers if step-based eval strategy and final step
                # isn't already an eval step (to avoid duplicate evaluation)
                if (
                    step == trainer.state.max_steps
                    and trainer.args.eval_strategy == IntervalStrategy.STEPS
                    and step % trainer.args.eval_steps != 0
                    and trainer.args.eval_delay <= step
                ):
                    expected_events += evaluation_events.copy()
                if step % trainer.args.save_steps == 0 or step == trainer.state.max_steps:
                    expected_events.append("on_save")
            expected_events.append("on_epoch_end")
            if trainer.args.eval_strategy == IntervalStrategy.EPOCH:
                expected_events += evaluation_events.copy()
        expected_events += ["on_log", "on_train_end"]
        return expected_events