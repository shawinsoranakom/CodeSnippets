def read_state_dict(checkpoint_file, print_global_state=False, map_location=None):
    _, extension = os.path.splitext(checkpoint_file)
    if extension.lower() == ".safetensors":
        device = map_location or shared.weight_load_location or devices.get_optimal_device_name()

        if not shared.opts.disable_mmap_load_safetensors:
            pl_sd = safetensors.torch.load_file(checkpoint_file, device=device)
        else:
            pl_sd = safetensors.torch.load(open(checkpoint_file, 'rb').read())
            pl_sd = {k: v.to(device) for k, v in pl_sd.items()}
    else:
        pl_sd = torch.load(checkpoint_file, map_location=map_location or shared.weight_load_location)

    if print_global_state and "global_step" in pl_sd:
        print(f"Global Step: {pl_sd['global_step']}")

    sd = get_state_dict_from_checkpoint(pl_sd)
    return sd