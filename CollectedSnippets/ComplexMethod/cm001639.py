def create_infotext(p, all_prompts, all_seeds, all_subseeds, comments=None, iteration=0, position_in_batch=0, use_main_prompt=False, index=None, all_negative_prompts=None):
    """
    this function is used to generate the infotext that is stored in the generated images, it's contains the parameters that are required to generate the imagee
    Args:
        p: StableDiffusionProcessing
        all_prompts: list[str]
        all_seeds: list[int]
        all_subseeds: list[int]
        comments: list[str]
        iteration: int
        position_in_batch: int
        use_main_prompt: bool
        index: int
        all_negative_prompts: list[str]

    Returns: str

    Extra generation params
    p.extra_generation_params dictionary allows for additional parameters to be added to the infotext
    this can be use by the base webui or extensions.
    To add a new entry, add a new key value pair, the dictionary key will be used as the key of the parameter in the infotext
    the value generation_params can be defined as:
        - str | None
        - List[str|None]
        - callable func(**kwargs) -> str | None

    When defined as a string, it will be used as without extra processing; this is this most common use case.

    Defining as a list allows for parameter that changes across images in the job, for example, the 'Seed' parameter.
    The list should have the same length as the total number of images in the entire job.

    Defining as a callable function allows parameter cannot be generated earlier or when extra logic is required.
    For example 'Hires prompt', due to reasons the hr_prompt might be changed by process in the pipeline or extensions
    and may vary across different images, defining as a static string or list would not work.

    The function takes locals() as **kwargs, as such will have access to variables like 'p' and 'index'.
    the base signature of the function should be:
        func(**kwargs) -> str | None
    optionally it can have additional arguments that will be used in the function:
        func(p, index, **kwargs) -> str | None
    note: for better future compatibility even though this function will have access to all variables in the locals(),
        it is recommended to only use the arguments present in the function signature of create_infotext.
    For actual implementation examples, see StableDiffusionProcessingTxt2Img.init > get_hr_prompt.
    """

    if use_main_prompt:
        index = 0
    elif index is None:
        index = position_in_batch + iteration * p.batch_size

    if all_negative_prompts is None:
        all_negative_prompts = p.all_negative_prompts

    clip_skip = getattr(p, 'clip_skip', opts.CLIP_stop_at_last_layers)
    enable_hr = getattr(p, 'enable_hr', False)
    token_merging_ratio = p.get_token_merging_ratio()
    token_merging_ratio_hr = p.get_token_merging_ratio(for_hr=True)

    prompt_text = p.main_prompt if use_main_prompt else all_prompts[index]
    negative_prompt = p.main_negative_prompt if use_main_prompt else all_negative_prompts[index]

    uses_ensd = opts.eta_noise_seed_delta != 0
    if uses_ensd:
        uses_ensd = sd_samplers_common.is_sampler_using_eta_noise_seed_delta(p)

    generation_params = {
        "Steps": p.steps,
        "Sampler": p.sampler_name,
        "Schedule type": p.scheduler,
        "CFG scale": p.cfg_scale,
        "Image CFG scale": getattr(p, 'image_cfg_scale', None),
        "Seed": p.all_seeds[0] if use_main_prompt else all_seeds[index],
        "Face restoration": opts.face_restoration_model if p.restore_faces else None,
        "Size": f"{p.width}x{p.height}",
        "Model hash": p.sd_model_hash if opts.add_model_hash_to_info else None,
        "Model": p.sd_model_name if opts.add_model_name_to_info else None,
        "FP8 weight": opts.fp8_storage if devices.fp8 else None,
        "Cache FP16 weight for LoRA": opts.cache_fp16_weight if devices.fp8 else None,
        "VAE hash": p.sd_vae_hash if opts.add_vae_hash_to_info else None,
        "VAE": p.sd_vae_name if opts.add_vae_name_to_info else None,
        "Variation seed": (None if p.subseed_strength == 0 else (p.all_subseeds[0] if use_main_prompt else all_subseeds[index])),
        "Variation seed strength": (None if p.subseed_strength == 0 else p.subseed_strength),
        "Seed resize from": (None if p.seed_resize_from_w <= 0 or p.seed_resize_from_h <= 0 else f"{p.seed_resize_from_w}x{p.seed_resize_from_h}"),
        "Denoising strength": p.extra_generation_params.get("Denoising strength"),
        "Conditional mask weight": getattr(p, "inpainting_mask_weight", shared.opts.inpainting_mask_weight) if p.is_using_inpainting_conditioning else None,
        "Clip skip": None if clip_skip <= 1 else clip_skip,
        "ENSD": opts.eta_noise_seed_delta if uses_ensd else None,
        "Token merging ratio": None if token_merging_ratio == 0 else token_merging_ratio,
        "Token merging ratio hr": None if not enable_hr or token_merging_ratio_hr == 0 else token_merging_ratio_hr,
        "Init image hash": getattr(p, 'init_img_hash', None),
        "RNG": opts.randn_source if opts.randn_source != "GPU" else None,
        "Tiling": "True" if p.tiling else None,
        **p.extra_generation_params,
        "Version": program_version() if opts.add_version_to_infotext else None,
        "User": p.user if opts.add_user_name_to_info else None,
    }

    for key, value in generation_params.items():
        try:
            if isinstance(value, list):
                generation_params[key] = value[index]
            elif callable(value):
                generation_params[key] = value(**locals())
        except Exception:
            errors.report(f'Error creating infotext for key "{key}"', exc_info=True)
            generation_params[key] = None

    generation_params_text = ", ".join([k if k == v else f'{k}: {infotext_utils.quote(v)}' for k, v in generation_params.items() if v is not None])

    negative_prompt_text = f"\nNegative prompt: {negative_prompt}" if negative_prompt else ""

    return f"{prompt_text}{negative_prompt_text}\n{generation_params_text}".strip()