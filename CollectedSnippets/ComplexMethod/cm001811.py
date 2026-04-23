def test_load_best_model_with_save(self):
        tmp_dir = self.get_auto_remove_tmp_dir()
        trainer = get_regression_trainer(
            output_dir=tmp_dir,
            save_steps=5,
            eval_strategy="steps",
            eval_steps=5,
            max_steps=9,
        )
        trainer.train()
        # Check that we have the last known step:
        assert os.path.exists(os.path.join(tmp_dir, f"checkpoint-{trainer.state.max_steps}")), (
            f"Could not find checkpoint-{trainer.state.max_steps}"
        )
        # And then check the last step
        assert os.path.exists(os.path.join(tmp_dir, "checkpoint-9")), "Could not find checkpoint-9"

        # Now test that using a limit works
        # Should result in:
        # - save at step 5 (but is deleted)
        # - save at step 10 (loaded in at the end when `load_best_model=True`)
        # - save at step 11
        tmp_dir = self.get_auto_remove_tmp_dir()
        trainer = get_regression_trainer(
            output_dir=tmp_dir,
            save_steps=5,
            eval_strategy="steps",
            eval_steps=5,
            load_best_model_at_end=True,
            save_total_limit=2,
            max_steps=11,
        )
        trainer.train()
        # Check that we have the last known step:
        assert os.path.exists(os.path.join(tmp_dir, "checkpoint-11")), "Could not find checkpoint-11"
        # And then check the last multiple
        assert os.path.exists(os.path.join(tmp_dir, "checkpoint-10")), "Could not find checkpoint-10"
        # Finally check that we don't have an old one
        assert not os.path.exists(os.path.join(tmp_dir, "checkpoint-5")), "Found checkpoint-5, limit not respected"

        # Finally check that the right model was loaded in - it should be the checkpoint
        # with the best eval metric. With eval at steps 5, 10, 11, the best could be any of them.
        model_state = trainer.model.state_dict()
        # Find which checkpoint has the best metric
        best_checkpoint_dir = trainer.state.best_model_checkpoint
        final_model_weights = safetensors.torch.load_file(os.path.join(best_checkpoint_dir, "model.safetensors"))
        for k, v in model_state.items():
            assert torch.allclose(v, final_model_weights[k]), f"{k} is not the same"