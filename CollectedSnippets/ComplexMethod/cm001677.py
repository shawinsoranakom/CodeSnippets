def text2imgapi(self, txt2imgreq: models.StableDiffusionTxt2ImgProcessingAPI):
        task_id = txt2imgreq.force_task_id or create_task_id("txt2img")

        script_runner = scripts.scripts_txt2img

        infotext_script_args = {}
        self.apply_infotext(txt2imgreq, "txt2img", script_runner=script_runner, mentioned_script_args=infotext_script_args)

        selectable_scripts, selectable_script_idx = self.get_selectable_script(txt2imgreq.script_name, script_runner)
        sampler, scheduler = sd_samplers.get_sampler_and_scheduler(txt2imgreq.sampler_name or txt2imgreq.sampler_index, txt2imgreq.scheduler)

        populate = txt2imgreq.copy(update={  # Override __init__ params
            "sampler_name": validate_sampler_name(sampler),
            "do_not_save_samples": not txt2imgreq.save_images,
            "do_not_save_grid": not txt2imgreq.save_images,
        })
        if populate.sampler_name:
            populate.sampler_index = None  # prevent a warning later on

        if not populate.scheduler and scheduler != "Automatic":
            populate.scheduler = scheduler

        args = vars(populate)
        args.pop('script_name', None)
        args.pop('script_args', None) # will refeed them to the pipeline directly after initializing them
        args.pop('alwayson_scripts', None)
        args.pop('infotext', None)

        script_args = self.init_script_args(txt2imgreq, self.default_script_arg_txt2img, selectable_scripts, selectable_script_idx, script_runner, input_script_args=infotext_script_args)

        send_images = args.pop('send_images', True)
        args.pop('save_images', None)

        add_task_to_queue(task_id)

        with self.queue_lock:
            with closing(StableDiffusionProcessingTxt2Img(sd_model=shared.sd_model, **args)) as p:
                p.is_api = True
                p.scripts = script_runner
                p.outpath_grids = opts.outdir_txt2img_grids
                p.outpath_samples = opts.outdir_txt2img_samples

                try:
                    shared.state.begin(job="scripts_txt2img")
                    start_task(task_id)
                    if selectable_scripts is not None:
                        p.script_args = script_args
                        processed = scripts.scripts_txt2img.run(p, *p.script_args) # Need to pass args as list here
                    else:
                        p.script_args = tuple(script_args) # Need to pass args as tuple here
                        processed = process_images(p)
                    finish_task(task_id)
                finally:
                    shared.state.end()
                    shared.total_tqdm.clear()

        b64images = list(map(encode_pil_to_base64, processed.images)) if send_images else []

        return models.TextToImageResponse(images=b64images, parameters=vars(txt2imgreq), info=processed.js())