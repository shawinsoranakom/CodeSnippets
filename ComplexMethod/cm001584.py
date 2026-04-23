def apply_optimizations(option=None):
    global current_optimizer

    undo_optimizations()

    if len(optimizers) == 0:
        # a script can access the model very early, and optimizations would not be filled by then
        current_optimizer = None
        return ''

    ldm.modules.diffusionmodules.model.nonlinearity = silu
    ldm.modules.diffusionmodules.openaimodel.th = sd_hijack_unet.th

    sgm.modules.diffusionmodules.model.nonlinearity = silu
    sgm.modules.diffusionmodules.openaimodel.th = sd_hijack_unet.th

    if current_optimizer is not None:
        current_optimizer.undo()
        current_optimizer = None

    selection = option or shared.opts.cross_attention_optimization
    if selection == "Automatic" and len(optimizers) > 0:
        matching_optimizer = next(iter([x for x in optimizers if x.cmd_opt and getattr(shared.cmd_opts, x.cmd_opt, False)]), optimizers[0])
    else:
        matching_optimizer = next(iter([x for x in optimizers if x.title() == selection]), None)

    if selection == "None":
        matching_optimizer = None
    elif selection == "Automatic" and shared.cmd_opts.disable_opt_split_attention:
        matching_optimizer = None
    elif matching_optimizer is None:
        matching_optimizer = optimizers[0]

    if matching_optimizer is not None:
        print(f"Applying attention optimization: {matching_optimizer.name}... ", end='')
        matching_optimizer.apply()
        print("done.")
        current_optimizer = matching_optimizer
        return current_optimizer.name
    else:
        print("Disabling attention optimization")
        return ''