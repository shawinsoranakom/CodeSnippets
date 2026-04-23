def __init__(self, target=None, embedding_directory=None, no_init=False, tokenizer_data={}, parameters=0, state_dict=[], model_options={}, disable_dynamic=False):
        if no_init:
            return
        params = target.params.copy()
        clip = target.clip
        tokenizer = target.tokenizer

        load_device = model_options.get("load_device", model_management.text_encoder_device())
        offload_device = model_options.get("offload_device", model_management.text_encoder_offload_device())
        dtype = model_options.get("dtype", None)
        if dtype is None:
            dtype = model_management.text_encoder_dtype(load_device)

        params['dtype'] = dtype
        params['device'] = model_options.get("initial_device", model_management.text_encoder_initial_device(load_device, offload_device, parameters * model_management.dtype_size(dtype)))
        params['model_options'] = model_options

        self.cond_stage_model = clip(**(params))

        for dt in self.cond_stage_model.dtypes:
            if not model_management.supports_cast(load_device, dt):
                load_device = offload_device
                if params['device'] != offload_device:
                    self.cond_stage_model.to(offload_device)
                    logging.warning("Had to shift TE back.")

        model_management.archive_model_dtypes(self.cond_stage_model)

        self.tokenizer = tokenizer(embedding_directory=embedding_directory, tokenizer_data=tokenizer_data)
        ModelPatcher = comfy.model_patcher.ModelPatcher if disable_dynamic else comfy.model_patcher.CoreModelPatcher
        self.patcher = ModelPatcher(self.cond_stage_model, load_device=load_device, offload_device=offload_device)
        #Match torch.float32 hardcode upcast in TE implemention
        self.patcher.set_model_compute_dtype(torch.float32)
        self.patcher.hook_mode = comfy.hooks.EnumHookMode.MinVram
        self.patcher.is_clip = True
        self.apply_hooks_to_conds = None
        if len(state_dict) > 0:
            if isinstance(state_dict, list):
                for c in state_dict:
                    m, u = self.load_sd(c)
                    if len(m) > 0:
                        logging.warning("clip missing: {}".format(m))

                    if len(u) > 0:
                        logging.debug("clip unexpected: {}".format(u))
            else:
                m, u = self.load_sd(state_dict, full_model=True)
                if len(m) > 0:
                    m_filter = list(filter(lambda a: ".logit_scale" not in a and ".transformer.text_projection.weight" not in a, m))
                    if len(m_filter) > 0:
                        logging.warning("clip missing: {}".format(m))
                    else:
                        logging.debug("clip missing: {}".format(m))

                if len(u) > 0:
                    logging.debug("clip unexpected {}:".format(u))

        if params['device'] == load_device:
            model_management.load_models_gpu([self.patcher], force_full_load=True)
        self.layer_idx = None
        self.use_clip_schedule = False
        logging.info("CLIP/text encoder model load device: {}, offload device: {}, current: {}, dtype: {}".format(load_device, offload_device, params['device'], dtype))
        self.tokenizer_options = {}