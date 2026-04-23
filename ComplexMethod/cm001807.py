def _run_translation(
        self,
        distributed=False,
        extra_args_str=None,
        predict_with_generate=True,
        do_train=True,
        do_eval=True,
        do_predict=True,
        n_gpus_to_use=None,
    ):
        data_dir = self.test_file_dir / "../fixtures/tests_samples/wmt_en_ro"
        output_dir = self.get_auto_remove_tmp_dir()
        args = f"""
            --model_name_or_path {MBART_TINY}
            --train_file {data_dir}/train.json
            --validation_file {data_dir}/val.json
            --test_file {data_dir}/test.json
            --output_dir {output_dir}
            --max_train_samples 8
            --max_source_length 12
            --max_target_length 12
            --do_train
            --num_train_epochs 1
            --per_device_train_batch_size 4
            --learning_rate 3e-3
            --warmup_steps 8
            --logging_steps 0
            --logging_strategy no
            --save_steps 1
            --train_sampling_strategy group_by_length
            --label_smoothing_factor 0.1
            --target_lang ro_RO
            --source_lang en_XX
            --report_to none
        """.split()

        if do_eval:
            args += """
                --do_eval
                --per_device_eval_batch_size 4
                --max_eval_samples 8
                --val_max_target_length 12
                --eval_strategy steps
                --eval_steps 1
            """.split()

        if do_predict:
            args += ["--do_predict"]

        if predict_with_generate:
            args += ["--predict_with_generate"]

        if do_train:
            args += ["--optim", "adafactor"]

        if extra_args_str is not None:
            args += extra_args_str.split()

        if distributed:
            if n_gpus_to_use is None:
                n_gpus_to_use = backend_device_count(torch_device)
            master_port = get_torch_dist_unique_port()
            distributed_args = f"""
                -m torch.distributed.run
                --nproc_per_node={n_gpus_to_use}
                --master_port={master_port}
                {self.examples_dir_str}/pytorch/translation/run_translation.py
            """.split()
            cmd = [sys.executable] + distributed_args + args
            execute_subprocess_async(cmd, env=self.get_env())
        else:
            testargs = ["run_translation.py"] + args
            with patch.object(sys, "argv", testargs):
                self._run_translation_main()

        return output_dir