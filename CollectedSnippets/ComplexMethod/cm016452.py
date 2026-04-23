def load_torch_file(ckpt, safe_load=False, device=None, return_metadata=False):
    if device is None:
        device = torch.device("cpu")
    metadata = None
    if ckpt.lower().endswith(".safetensors") or ckpt.lower().endswith(".sft"):
        try:
            if comfy.memory_management.aimdo_enabled:
                sd, metadata = load_safetensors(ckpt)
                if not return_metadata:
                    metadata = None
            else:
                with safetensors.safe_open(ckpt, framework="pt", device=device.type) as f:
                    sd = {}
                    for k in f.keys():
                        tensor = f.get_tensor(k)
                        if DISABLE_MMAP:  # TODO: Not sure if this is the best way to bypass the mmap issues
                            tensor = tensor.to(device=device, copy=True)
                        sd[k] = tensor
                    if return_metadata:
                        metadata = f.metadata()
        except Exception as e:
            if len(e.args) > 0:
                message = e.args[0]
                if "HeaderTooLarge" in message:
                    raise ValueError("{}\n\nFile path: {}\n\nThe safetensors file is corrupt or invalid. Make sure this is actually a safetensors file and not a ckpt or pt or other filetype.".format(message, ckpt))
                if "MetadataIncompleteBuffer" in message:
                    raise ValueError("{}\n\nFile path: {}\n\nThe safetensors file is corrupt/incomplete. Check the file size and make sure you have copied/downloaded it correctly.".format(message, ckpt))
            raise e
    else:
        torch_args = {}
        if MMAP_TORCH_FILES:
            torch_args["mmap"] = True

        pl_sd = torch.load(ckpt, map_location=device, weights_only=True, **torch_args)

        if "state_dict" in pl_sd:
            sd = pl_sd["state_dict"]
        else:
            if len(pl_sd) == 1:
                key = list(pl_sd.keys())[0]
                sd = pl_sd[key]
                if not isinstance(sd, dict):
                    sd = pl_sd
            else:
                sd = pl_sd
    return (sd, metadata) if return_metadata else sd