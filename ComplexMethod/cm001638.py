def decode_latent_batch(model, batch, target_device=None, check_for_nans=False):
    samples = DecodedSamples()

    if check_for_nans:
        devices.test_for_nans(batch, "unet")

    for i in range(batch.shape[0]):
        sample = decode_first_stage(model, batch[i:i + 1])[0]

        if check_for_nans:

            try:
                devices.test_for_nans(sample, "vae")
            except devices.NansException as e:
                if shared.opts.auto_vae_precision_bfloat16:
                    autofix_dtype = torch.bfloat16
                    autofix_dtype_text = "bfloat16"
                    autofix_dtype_setting = "Automatically convert VAE to bfloat16"
                    autofix_dtype_comment = ""
                elif shared.opts.auto_vae_precision:
                    autofix_dtype = torch.float32
                    autofix_dtype_text = "32-bit float"
                    autofix_dtype_setting = "Automatically revert VAE to 32-bit floats"
                    autofix_dtype_comment = "\nTo always start with 32-bit VAE, use --no-half-vae commandline flag."
                else:
                    raise e

                if devices.dtype_vae == autofix_dtype:
                    raise e

                errors.print_error_explanation(
                    "A tensor with all NaNs was produced in VAE.\n"
                    f"Web UI will now convert VAE into {autofix_dtype_text} and retry.\n"
                    f"To disable this behavior, disable the '{autofix_dtype_setting}' setting.{autofix_dtype_comment}"
                )

                devices.dtype_vae = autofix_dtype
                model.first_stage_model.to(devices.dtype_vae)
                batch = batch.to(devices.dtype_vae)

                sample = decode_first_stage(model, batch[i:i + 1])[0]

        if target_device is not None:
            sample = sample.to(target_device)

        samples.append(sample)

    return samples