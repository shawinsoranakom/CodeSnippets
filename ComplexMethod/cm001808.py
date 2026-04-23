def test_run_seq2seq_slow(self):
        output_dir = self._run_translation(
            extra_args_str=f"--model_name_or_path {MARIAN_MODEL} --learning_rate 3e-4 --num_train_epochs 10 --max_source_length 128 --max_target_length 128 --eval_steps 2 --save_steps 2",
        )
        logs = TrainerState.load_from_json(os.path.join(output_dir, "trainer_state.json")).log_history
        eval_metrics = [log for log in logs if "eval_loss" in log]
        first_step_stats = eval_metrics[0]
        last_step_stats = eval_metrics[-1]
        assert first_step_stats["eval_loss"] > last_step_stats["eval_loss"], "model learned nothing"
        assert isinstance(last_step_stats["eval_bleu"], float)
        contents = {os.path.basename(p) for p in os.listdir(output_dir)}
        assert "generated_predictions.txt" in contents
        assert "predict_results.json" in contents