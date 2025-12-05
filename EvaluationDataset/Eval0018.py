class TestDeepSpeedModelZoo(TestCasePlus):

    def get_task_cmd(self, task, stage):
        if task not in task_cmds:
            raise ValueError(f"don't know of task {task}, have {task_cmds.keys()}")

        cmd = task_cmds[task]
        args_ds = f"--deepspeed {self.test_file_dir_str}/ds_config_{stage}.json".split()

        output_dir = self.get_auto_remove_tmp_dir()
        args_out = f"--output_dir {output_dir}".split()

        cmd += args_ds + args_out

        return cmd, output_dir

    def test_zero_to_fp32(self, stage, task):

        cmd, output_dir = self.get_task_cmd(task, stage)

        cmd += "--save_steps 1".split()

        execute_subprocess_async(cmd, env=self.get_env())

        chkpt_dir = f"{output_dir}/checkpoint-1"
        recovered_model_path = f"{chkpt_dir}/out.bin"
        cmd = f"{chkpt_dir}/zero_to_fp32.py {chkpt_dir} {recovered_model_path}"

        subprocess.check_call(cmd, shell=True)
        assert os.path.exists(recovered_model_path), f"{recovered_model_path} was not found"
