def test_best_model_checkpoint_behavior(self):
        # Case 1. No evaluation, save_total_limit > 1 and save_steps == 1.
        # Both best_metric and best_model_checkpoint should be None.
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = get_regression_trainer(
                output_dir=tmpdir,
                eval_strategy="no",
                save_strategy="steps",
                save_steps=1,
                metric_for_best_model="accuracy",
                greater_is_better=True,
            )
            trainer.train()

            assert trainer.state.best_metric is None
            assert trainer.state.best_model_checkpoint is None
            assert len(os.listdir(tmpdir)) == trainer.state.global_step

        # Case 2. No evaluation and save_total_limit == 1.
        # Both best_metric and best_model_checkpoint should be None.
        # Only the last checkpoint should remain.
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = get_regression_trainer(
                output_dir=tmpdir,
                eval_strategy="no",
                save_strategy="steps",
                save_steps=1,
                metric_for_best_model="accuracy",
                greater_is_better=True,
                save_total_limit=1,
            )
            trainer.train()

            num_steps = trainer.state.global_step

            assert trainer.state.best_metric is None
            assert trainer.state.best_model_checkpoint is None
            assert len(os.listdir(tmpdir)) == 1

            ckpt = os.path.join(tmpdir, f"{PREFIX_CHECKPOINT_DIR}-{num_steps}")
            assert os.path.isdir(ckpt)
            assert os.listdir(tmpdir)[0] == f"{PREFIX_CHECKPOINT_DIR}-{num_steps}"

        # Case 3. eval_strategy == save_strategy.
        # best_model_checkpoint should be at epoch 1.
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = get_regression_trainer(
                output_dir=tmpdir,
                eval_strategy="epoch",
                save_strategy="epoch",
                metric_for_best_model="accuracy",
                compute_metrics=AlmostAccuracy(),
                greater_is_better=True,
                load_best_model_at_end=False,
            )

            with patch.object(
                trainer,
                "_evaluate",
                side_effect=evaluate_side_effect_factory(
                    [
                        {"eval_accuracy": 0.59},
                        {"eval_accuracy": 0.57},
                        {"eval_accuracy": 0.55},
                    ]
                ),
            ):
                trainer.train()

            steps_per_epoch = get_steps_per_epoch(trainer)

            assert trainer.state.best_metric == 0.59
            assert trainer.state.best_global_step == steps_per_epoch

            best_ckpt = os.path.join(tmpdir, f"{PREFIX_CHECKPOINT_DIR}-{trainer.state.best_global_step}")
            assert trainer.state.best_model_checkpoint == best_ckpt

            assert len(os.listdir(tmpdir)) == trainer.state.num_train_epochs

        # Case 4. eval_strategy != save_strategy.
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = get_regression_trainer(
                output_dir=tmpdir,
                eval_strategy="epoch",
                save_strategy="steps",
                save_steps=1,
                metric_for_best_model="accuracy",
                compute_metrics=AlmostAccuracy(),
                greater_is_better=True,
                load_best_model_at_end=False,
            )

            with patch.object(
                trainer,
                "_evaluate",
                side_effect=evaluate_side_effect_factory(
                    [
                        {"eval_accuracy": 0.59},
                        {"eval_accuracy": 0.57},
                        {"eval_accuracy": 0.55},
                    ]
                ),
            ):
                trainer.train()

            steps_per_epoch = get_steps_per_epoch(trainer)

            assert trainer.state.best_metric == 0.59
            assert trainer.state.best_global_step == steps_per_epoch

            best_ckpt = os.path.join(tmpdir, f"{PREFIX_CHECKPOINT_DIR}-{trainer.state.best_global_step}")
            assert trainer.state.best_model_checkpoint == best_ckpt

            assert len(os.listdir(tmpdir)) == trainer.state.global_step

        # Case 5. Multiple checkpoints, save_total_limit == 1.
        # Best metric is found at step 1 and that checkpoint should be saved.
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = get_regression_trainer(
                output_dir=tmpdir,
                eval_strategy="steps",
                eval_steps=1,
                save_strategy="steps",
                save_steps=1,
                metric_for_best_model="accuracy",
                compute_metrics=AlmostAccuracy(),
                greater_is_better=True,
                save_total_limit=1,
            )

            with patch.object(
                trainer,
                "_evaluate",
                side_effect=evaluate_side_effect_factory(
                    [
                        {"eval_accuracy": 0.90},
                        {"eval_accuracy": 0.80},
                        {"eval_accuracy": 0.70},
                    ]
                ),
            ):
                trainer.train()

            assert trainer.state.best_metric == 0.90
            assert trainer.state.best_global_step == 1

            best_ckpt = os.path.join(tmpdir, f"{PREFIX_CHECKPOINT_DIR}-{trainer.state.best_global_step}")
            assert trainer.state.best_model_checkpoint == best_ckpt

            assert len(os.listdir(tmpdir)) == 1

        # Case 6. Saving happens more often and eval/save mismatch.
        # `best_model_checkpoint` should be None due to a step mismatch.
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = get_regression_trainer(
                output_dir=tmpdir,
                eval_strategy="steps",
                eval_steps=3,
                save_strategy="steps",
                save_steps=2,
                metric_for_best_model="accuracy",
                compute_metrics=AlmostAccuracy(),
                greater_is_better=True,
            )

            with patch.object(
                trainer,
                "_evaluate",
                side_effect=evaluate_side_effect_factory(
                    [
                        {"eval_accuracy": 0.90},
                        {"eval_accuracy": 0.80},
                        {"eval_accuracy": 0.70},
                    ]
                ),
            ):
                trainer.train()

            assert trainer.state.best_metric == 0.90
            assert trainer.state.best_global_step == 3

            assert trainer.state.best_model_checkpoint is None

            assert len(os.listdir(tmpdir)) == trainer.state.global_step // 2