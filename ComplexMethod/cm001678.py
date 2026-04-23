def img2imgapi(self, img2imgreq: models.StableDiffusionImg2ImgProcessingAPI):
        task_id = img2imgreq.force_task_id or create_task_id("img2img")

        init_images = img2imgreq.init_images
        if init_images is None:
            raise HTTPException(status_code=404, detail="Init image not found")

        mask = img2imgreq.mask
        if mask:
            mask = decode_base64_to_image(mask)

        script_runner = scripts.scripts_img2img

        infotext_script_args = {}
        self.apply_infotext(img2imgreq, "img2img", script_runner=script_runner, mentioned_script_args=infotext_script_args)

        selectable_scripts, selectable_script_idx = self.get_selectable_script(img2imgreq.script_name, script_runner)
        sampler, scheduler = sd_samplers.get_sampler_and_scheduler(img2imgreq.sampler_name or img2imgreq.sampler_index, img2imgreq.scheduler)

        populate = img2imgreq.copy(update={  # Override __init__ params
            "sampler_name": validate_sampler_name(sampler),
            "do_not_save_samples": not img2imgreq.save_images,
            "do_not_save_grid": not img2imgreq.save_images,
            "mask": mask,
        })
        if populate.sampler_name:
            populate.sampler_index = None  # prevent a warning later on

        if not populate.scheduler and scheduler != "Automatic":
            populate.scheduler = scheduler

        args = vars(populate)
        args.pop('include_init_images', None)  # this is meant to be done by "exclude": True in model, but it's for a reason that I cannot determine.
        args.pop('script_name', None)
        args.pop('script_args', None)  # will refeed them to the pipeline directly after initializing them
        args.pop('alwayson_scripts', None)
        args.pop('infotext', None)

        script_args = self.init_script_args(img2imgreq, self.default_script_arg_img2img, selectable_scripts, selectable_script_idx, script_runner, input_script_args=infotext_script_args)

        send_images = args.pop('send_images', True)
        args.pop('save_images', None)

        add_task_to_queue(task_id)

        with self.queue_lock:
            with closing(StableDiffusionProcessingImg2Img(sd_model=shared.sd_model, **args)) as p:
                p.init_images = [decode_base64_to_image(x) for x in init_images]
                p.is_api = True
                p.scripts = script_runner
                p.outpath_grids = opts.outdir_img2img_grids
                p.outpath_samples = opts.outdir_img2img_samples

                try:
                    shared.state.begin(job="scripts_img2img")
                    start_task(task_id)
                    if selectable_scripts is not None:
                        p.script_args = script_args
                        processed = scripts.scripts_img2img.run(p, *p.script_args) # Need to pass args as list here
                    else:
                        p.script_args = tuple(script_args) # Need to pass args as tuple here
                        processed = process_images(p)
                    finish_task(task_id)
                finally:
                    shared.state.end()
                    shared.total_tqdm.clear()

        b64images = list(map(encode_pil_to_base64, processed.images)) if send_images else []

        if not img2imgreq.include_init_images:
            img2imgreq.init_images = None
            img2imgreq.mask = None

        return models.ImageToImageResponse(images=b64images, parameters=vars(img2imgreq), info=processed.js())