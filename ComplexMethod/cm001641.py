def process_images_inner(p: StableDiffusionProcessing) -> Processed:
    """this is the main loop that both txt2img and img2img use; it calls func_init once inside all the scopes and func_sample once per batch"""

    if isinstance(p.prompt, list):
        assert(len(p.prompt) > 0)
    else:
        assert p.prompt is not None

    devices.torch_gc()

    seed = get_fixed_seed(p.seed)
    subseed = get_fixed_seed(p.subseed)

    if p.restore_faces is None:
        p.restore_faces = opts.face_restoration

    if p.tiling is None:
        p.tiling = opts.tiling

    if p.refiner_checkpoint not in (None, "", "None", "none"):
        p.refiner_checkpoint_info = sd_models.get_closet_checkpoint_match(p.refiner_checkpoint)
        if p.refiner_checkpoint_info is None:
            raise Exception(f'Could not find checkpoint with name {p.refiner_checkpoint}')

    if hasattr(shared.sd_model, 'fix_dimensions'):
        p.width, p.height = shared.sd_model.fix_dimensions(p.width, p.height)

    p.sd_model_name = shared.sd_model.sd_checkpoint_info.name_for_extra
    p.sd_model_hash = shared.sd_model.sd_model_hash
    p.sd_vae_name = sd_vae.get_loaded_vae_name()
    p.sd_vae_hash = sd_vae.get_loaded_vae_hash()

    modules.sd_hijack.model_hijack.apply_circular(p.tiling)
    modules.sd_hijack.model_hijack.clear_comments()

    p.fill_fields_from_opts()
    p.setup_prompts()

    if isinstance(seed, list):
        p.all_seeds = seed
    else:
        p.all_seeds = [int(seed) + (x if p.subseed_strength == 0 else 0) for x in range(len(p.all_prompts))]

    if isinstance(subseed, list):
        p.all_subseeds = subseed
    else:
        p.all_subseeds = [int(subseed) + x for x in range(len(p.all_prompts))]

    if os.path.exists(cmd_opts.embeddings_dir) and not p.do_not_reload_embeddings:
        model_hijack.embedding_db.load_textual_inversion_embeddings()

    if p.scripts is not None:
        p.scripts.process(p)

    infotexts = []
    output_images = []
    with torch.no_grad(), p.sd_model.ema_scope():
        with devices.autocast():
            p.init(p.all_prompts, p.all_seeds, p.all_subseeds)

            # for OSX, loading the model during sampling changes the generated picture, so it is loaded here
            if shared.opts.live_previews_enable and opts.show_progress_type == "Approx NN":
                sd_vae_approx.model()

            sd_unet.apply_unet()

        if state.job_count == -1:
            state.job_count = p.n_iter

        for n in range(p.n_iter):
            p.iteration = n

            if state.skipped:
                state.skipped = False

            if state.interrupted or state.stopping_generation:
                break

            sd_models.reload_model_weights()  # model can be changed for example by refiner

            p.prompts = p.all_prompts[n * p.batch_size:(n + 1) * p.batch_size]
            p.negative_prompts = p.all_negative_prompts[n * p.batch_size:(n + 1) * p.batch_size]
            p.seeds = p.all_seeds[n * p.batch_size:(n + 1) * p.batch_size]
            p.subseeds = p.all_subseeds[n * p.batch_size:(n + 1) * p.batch_size]

            latent_channels = getattr(shared.sd_model, 'latent_channels', opt_C)
            p.rng = rng.ImageRNG((latent_channels, p.height // opt_f, p.width // opt_f), p.seeds, subseeds=p.subseeds, subseed_strength=p.subseed_strength, seed_resize_from_h=p.seed_resize_from_h, seed_resize_from_w=p.seed_resize_from_w)

            if p.scripts is not None:
                p.scripts.before_process_batch(p, batch_number=n, prompts=p.prompts, seeds=p.seeds, subseeds=p.subseeds)

            if len(p.prompts) == 0:
                break

            p.parse_extra_network_prompts()

            if not p.disable_extra_networks:
                with devices.autocast():
                    extra_networks.activate(p, p.extra_network_data)

            if p.scripts is not None:
                p.scripts.process_batch(p, batch_number=n, prompts=p.prompts, seeds=p.seeds, subseeds=p.subseeds)

            p.setup_conds()

            p.extra_generation_params.update(model_hijack.extra_generation_params)

            # params.txt should be saved after scripts.process_batch, since the
            # infotext could be modified by that callback
            # Example: a wildcard processed by process_batch sets an extra model
            # strength, which is saved as "Model Strength: 1.0" in the infotext
            if n == 0 and not cmd_opts.no_prompt_history:
                with open(os.path.join(paths.data_path, "params.txt"), "w", encoding="utf8") as file:
                    processed = Processed(p, [])
                    file.write(processed.infotext(p, 0))

            for comment in model_hijack.comments:
                p.comment(comment)

            if p.n_iter > 1:
                shared.state.job = f"Batch {n+1} out of {p.n_iter}"

            sd_models.apply_alpha_schedule_override(p.sd_model, p)

            with devices.without_autocast() if devices.unet_needs_upcast else devices.autocast():
                samples_ddim = p.sample(conditioning=p.c, unconditional_conditioning=p.uc, seeds=p.seeds, subseeds=p.subseeds, subseed_strength=p.subseed_strength, prompts=p.prompts)

            if p.scripts is not None:
                ps = scripts.PostSampleArgs(samples_ddim)
                p.scripts.post_sample(p, ps)
                samples_ddim = ps.samples

            if getattr(samples_ddim, 'already_decoded', False):
                x_samples_ddim = samples_ddim
            else:
                devices.test_for_nans(samples_ddim, "unet")

                if opts.sd_vae_decode_method != 'Full':
                    p.extra_generation_params['VAE Decoder'] = opts.sd_vae_decode_method
                x_samples_ddim = decode_latent_batch(p.sd_model, samples_ddim, target_device=devices.cpu, check_for_nans=True)

            x_samples_ddim = torch.stack(x_samples_ddim).float()
            x_samples_ddim = torch.clamp((x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0)

            del samples_ddim

            if lowvram.is_enabled(shared.sd_model):
                lowvram.send_everything_to_cpu()

            devices.torch_gc()

            state.nextjob()

            if p.scripts is not None:
                p.scripts.postprocess_batch(p, x_samples_ddim, batch_number=n)

                p.prompts = p.all_prompts[n * p.batch_size:(n + 1) * p.batch_size]
                p.negative_prompts = p.all_negative_prompts[n * p.batch_size:(n + 1) * p.batch_size]

                batch_params = scripts.PostprocessBatchListArgs(list(x_samples_ddim))
                p.scripts.postprocess_batch_list(p, batch_params, batch_number=n)
                x_samples_ddim = batch_params.images

            def infotext(index=0, use_main_prompt=False):
                return create_infotext(p, p.prompts, p.seeds, p.subseeds, use_main_prompt=use_main_prompt, index=index, all_negative_prompts=p.negative_prompts)

            save_samples = p.save_samples()

            for i, x_sample in enumerate(x_samples_ddim):
                p.batch_index = i

                x_sample = 255. * np.moveaxis(x_sample.cpu().numpy(), 0, 2)
                x_sample = x_sample.astype(np.uint8)

                if p.restore_faces:
                    if save_samples and opts.save_images_before_face_restoration:
                        images.save_image(Image.fromarray(x_sample), p.outpath_samples, "", p.seeds[i], p.prompts[i], opts.samples_format, info=infotext(i), p=p, suffix="-before-face-restoration")

                    devices.torch_gc()

                    x_sample = modules.face_restoration.restore_faces(x_sample)
                    devices.torch_gc()

                image = Image.fromarray(x_sample)

                if p.scripts is not None:
                    pp = scripts.PostprocessImageArgs(image)
                    p.scripts.postprocess_image(p, pp)
                    image = pp.image

                mask_for_overlay = getattr(p, "mask_for_overlay", None)

                if not shared.opts.overlay_inpaint:
                    overlay_image = None
                elif getattr(p, "overlay_images", None) is not None and i < len(p.overlay_images):
                    overlay_image = p.overlay_images[i]
                else:
                    overlay_image = None

                if p.scripts is not None:
                    ppmo = scripts.PostProcessMaskOverlayArgs(i, mask_for_overlay, overlay_image)
                    p.scripts.postprocess_maskoverlay(p, ppmo)
                    mask_for_overlay, overlay_image = ppmo.mask_for_overlay, ppmo.overlay_image

                if p.color_corrections is not None and i < len(p.color_corrections):
                    if save_samples and opts.save_images_before_color_correction:
                        image_without_cc, _ = apply_overlay(image, p.paste_to, overlay_image)
                        images.save_image(image_without_cc, p.outpath_samples, "", p.seeds[i], p.prompts[i], opts.samples_format, info=infotext(i), p=p, suffix="-before-color-correction")
                    image = apply_color_correction(p.color_corrections[i], image)

                # If the intention is to show the output from the model
                # that is being composited over the original image,
                # we need to keep the original image around
                # and use it in the composite step.
                image, original_denoised_image = apply_overlay(image, p.paste_to, overlay_image)

                if p.scripts is not None:
                    pp = scripts.PostprocessImageArgs(image)
                    p.scripts.postprocess_image_after_composite(p, pp)
                    image = pp.image

                if save_samples:
                    images.save_image(image, p.outpath_samples, "", p.seeds[i], p.prompts[i], opts.samples_format, info=infotext(i), p=p)

                text = infotext(i)
                infotexts.append(text)
                if opts.enable_pnginfo:
                    image.info["parameters"] = text
                output_images.append(image)

                if mask_for_overlay is not None:
                    if opts.return_mask or opts.save_mask:
                        image_mask = mask_for_overlay.convert('RGB')
                        if save_samples and opts.save_mask:
                            images.save_image(image_mask, p.outpath_samples, "", p.seeds[i], p.prompts[i], opts.samples_format, info=infotext(i), p=p, suffix="-mask")
                        if opts.return_mask:
                            output_images.append(image_mask)

                    if opts.return_mask_composite or opts.save_mask_composite:
                        image_mask_composite = Image.composite(original_denoised_image.convert('RGBA').convert('RGBa'), Image.new('RGBa', image.size), images.resize_image(2, mask_for_overlay, image.width, image.height).convert('L')).convert('RGBA')
                        if save_samples and opts.save_mask_composite:
                            images.save_image(image_mask_composite, p.outpath_samples, "", p.seeds[i], p.prompts[i], opts.samples_format, info=infotext(i), p=p, suffix="-mask-composite")
                        if opts.return_mask_composite:
                            output_images.append(image_mask_composite)

            del x_samples_ddim

            devices.torch_gc()

        if not infotexts:
            infotexts.append(Processed(p, []).infotext(p, 0))

        p.color_corrections = None

        index_of_first_image = 0
        unwanted_grid_because_of_img_count = len(output_images) < 2 and opts.grid_only_if_multiple
        if (opts.return_grid or opts.grid_save) and not p.do_not_save_grid and not unwanted_grid_because_of_img_count:
            grid = images.image_grid(output_images, p.batch_size)

            if opts.return_grid:
                text = infotext(use_main_prompt=True)
                infotexts.insert(0, text)
                if opts.enable_pnginfo:
                    grid.info["parameters"] = text
                output_images.insert(0, grid)
                index_of_first_image = 1
            if opts.grid_save:
                images.save_image(grid, p.outpath_grids, "grid", p.all_seeds[0], p.all_prompts[0], opts.grid_format, info=infotext(use_main_prompt=True), short_filename=not opts.grid_extended_filename, p=p, grid=True)

    if not p.disable_extra_networks and p.extra_network_data:
        extra_networks.deactivate(p, p.extra_network_data)

    devices.torch_gc()

    res = Processed(
        p,
        images_list=output_images,
        seed=p.all_seeds[0],
        info=infotexts[0],
        subseed=p.all_subseeds[0],
        index_of_first_image=index_of_first_image,
        infotexts=infotexts,
    )

    if p.scripts is not None:
        p.scripts.postprocess(p, res)

    return res