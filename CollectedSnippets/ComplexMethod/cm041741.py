def load_model(self, data) -> Generator[str, None, None]:
        get = lambda elem_id: data[self.manager.get_elem_by_id(elem_id)]
        lang, model_name, model_path = get("top.lang"), get("top.model_name"), get("top.model_path")
        finetuning_type, checkpoint_path = get("top.finetuning_type"), get("top.checkpoint_path")
        user_config = load_config()

        error = ""
        if self.loaded:
            error = ALERTS["err_exists"][lang]
        elif not model_name:
            error = ALERTS["err_no_model"][lang]
        elif not model_path:
            error = ALERTS["err_no_path"][lang]
        elif self.demo_mode:
            error = ALERTS["err_demo"][lang]

        try:
            json.loads(get("infer.extra_args"))
        except json.JSONDecodeError:
            error = ALERTS["err_json_schema"][lang]

        if error:
            gr.Warning(error)
            yield error
            return

        yield ALERTS["info_loading"][lang]
        args = dict(
            model_name_or_path=model_path,
            cache_dir=user_config.get("cache_dir", None),
            finetuning_type=finetuning_type,
            template=get("top.template"),
            rope_scaling=get("top.rope_scaling") if get("top.rope_scaling") != "none" else None,
            flash_attn="fa2" if get("top.booster") == "flashattn2" else "auto",
            use_unsloth=(get("top.booster") == "unsloth"),
            enable_liger_kernel=(get("top.booster") == "liger_kernel"),
            infer_backend=get("infer.infer_backend"),
            infer_dtype=get("infer.infer_dtype"),
            trust_remote_code=True,
        )
        args.update(json.loads(get("infer.extra_args")))

        # checkpoints
        if checkpoint_path:
            if finetuning_type in PEFT_METHODS:  # list
                args["adapter_name_or_path"] = ",".join(
                    [get_save_dir(model_name, finetuning_type, adapter) for adapter in checkpoint_path]
                )
            else:  # str
                args["model_name_or_path"] = get_save_dir(model_name, finetuning_type, checkpoint_path)

        # quantization
        if get("top.quantization_bit") != "none":
            args["quantization_bit"] = int(get("top.quantization_bit"))
            args["quantization_method"] = get("top.quantization_method")
            args["double_quantization"] = not is_torch_npu_available()

        super().__init__(args)
        yield ALERTS["info_loaded"][lang]