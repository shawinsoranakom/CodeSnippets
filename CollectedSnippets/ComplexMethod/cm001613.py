def get_unet_option(option=None):
    option = option or shared.opts.sd_unet

    if option == "None":
        return None

    if option == "Automatic":
        name = shared.sd_model.sd_checkpoint_info.model_name

        options = [x for x in unet_options if x.model_name == name]

        option = options[0].label if options else "None"

    return next(iter([x for x in unet_options if x.label == option]), None)