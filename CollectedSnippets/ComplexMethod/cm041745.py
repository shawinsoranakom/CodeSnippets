def _parse_eval_args(self, data: dict["Component", Any]) -> dict[str, Any]:
        r"""Build and validate the evaluation arguments."""
        get = lambda elem_id: data[self.manager.get_elem_by_id(elem_id)]
        model_name, finetuning_type = get("top.model_name"), get("top.finetuning_type")
        user_config = load_config()

        args = dict(
            stage="sft",
            model_name_or_path=get("top.model_path"),
            cache_dir=user_config.get("cache_dir", None),
            preprocessing_num_workers=16,
            finetuning_type=finetuning_type,
            quantization_method=get("top.quantization_method"),
            template=get("top.template"),
            rope_scaling=get("top.rope_scaling") if get("top.rope_scaling") != "none" else None,
            flash_attn="fa2" if get("top.booster") == "flashattn2" else "auto",
            use_unsloth=(get("top.booster") == "unsloth"),
            dataset_dir=get("eval.dataset_dir"),
            eval_dataset=",".join(get("eval.dataset")),
            cutoff_len=get("eval.cutoff_len"),
            max_samples=int(get("eval.max_samples")),
            per_device_eval_batch_size=get("eval.batch_size"),
            predict_with_generate=True,
            report_to="none",
            max_new_tokens=get("eval.max_new_tokens"),
            top_p=get("eval.top_p"),
            temperature=get("eval.temperature"),
            output_dir=get_save_dir(model_name, finetuning_type, get("eval.output_dir")),
            trust_remote_code=True,
            ddp_timeout=180000000,
        )

        if get("eval.predict"):
            args["do_predict"] = True
        else:
            args["do_eval"] = True

        # checkpoints
        if get("top.checkpoint_path"):
            if finetuning_type in PEFT_METHODS:  # list
                args["adapter_name_or_path"] = ",".join(
                    [get_save_dir(model_name, finetuning_type, adapter) for adapter in get("top.checkpoint_path")]
                )
            else:  # str
                args["model_name_or_path"] = get_save_dir(model_name, finetuning_type, get("top.checkpoint_path"))

        # quantization
        if get("top.quantization_bit") != "none":
            args["quantization_bit"] = int(get("top.quantization_bit"))
            args["quantization_method"] = get("top.quantization_method")
            args["double_quantization"] = not is_torch_npu_available()

        return args