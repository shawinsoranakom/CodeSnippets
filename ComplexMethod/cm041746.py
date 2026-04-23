def monitor(self):
        r"""Monitorgit the training progress and logs."""
        self.aborted = False
        self.running = True

        get = lambda elem_id: self.running_data[self.manager.get_elem_by_id(elem_id)]
        lang, model_name, finetuning_type = get("top.lang"), get("top.model_name"), get("top.finetuning_type")
        output_dir = get("{}.output_dir".format("train" if self.do_train else "eval"))
        output_path = get_save_dir(model_name, finetuning_type, output_dir)

        output_box = self.manager.get_elem_by_id("{}.output_box".format("train" if self.do_train else "eval"))
        progress_bar = self.manager.get_elem_by_id("{}.progress_bar".format("train" if self.do_train else "eval"))
        loss_viewer = self.manager.get_elem_by_id("train.loss_viewer") if self.do_train else None
        swanlab_link = self.manager.get_elem_by_id("train.swanlab_link") if self.do_train else None

        running_log = ""
        return_code = -1
        while return_code == -1:
            if self.aborted:
                yield {
                    output_box: ALERTS["info_aborting"][lang],
                    progress_bar: gr.Slider(visible=False),
                }
            else:
                running_log, running_progress, running_info = get_trainer_info(lang, output_path, self.do_train)
                return_dict = {
                    output_box: running_log,
                    progress_bar: running_progress,
                }
                if "loss_viewer" in running_info:
                    return_dict[loss_viewer] = running_info["loss_viewer"]

                if "swanlab_link" in running_info:
                    return_dict[swanlab_link] = running_info["swanlab_link"]

                yield return_dict

            try:
                stderr = self.trainer.communicate(timeout=2)[1]
                return_code = self.trainer.returncode
            except TimeoutExpired:
                continue

        if return_code == 0 or self.aborted:
            finish_info = ALERTS["info_finished"][lang]
            if self.do_train:
                finish_log = ALERTS["info_finished"][lang] + "\n\n" + running_log
            else:
                finish_log = load_eval_results(os.path.join(output_path, "all_results.json")) + "\n\n" + running_log
        else:
            print(stderr)
            finish_info = ALERTS["err_failed"][lang]
            finish_log = ALERTS["err_failed"][lang] + f" Exit code: {return_code}\n\n```\n{stderr}\n```\n"

        self._finalize(lang, finish_info)
        return_dict = {output_box: finish_log, progress_bar: gr.Slider(visible=False)}
        yield return_dict