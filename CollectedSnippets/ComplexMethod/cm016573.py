def fix_empty_latent_channels(model, latent_image, downscale_ratio_spacial=None):
    if latent_image.is_nested:
        return latent_image
    latent_format = model.get_model_object("latent_format") #Resize the empty latent image so it has the right number of channels
    if torch.count_nonzero(latent_image) == 0:
        if latent_format.latent_channels != latent_image.shape[1]:
            latent_image = comfy.utils.repeat_to_batch_size(latent_image, latent_format.latent_channels, dim=1)
        if downscale_ratio_spacial is not None:
            if downscale_ratio_spacial != latent_format.spacial_downscale_ratio:
                ratio = downscale_ratio_spacial / latent_format.spacial_downscale_ratio
                latent_image = comfy.utils.common_upscale(latent_image, round(latent_image.shape[-1] * ratio), round(latent_image.shape[-2] * ratio), "nearest-exact", crop="disabled")

    if latent_format.latent_dimensions == 3 and latent_image.ndim == 4:
        latent_image = latent_image.unsqueeze(2)
    return latent_image