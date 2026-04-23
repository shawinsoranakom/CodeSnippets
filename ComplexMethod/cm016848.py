def _detect_and_load(cls, sd):
        # Try FILM
        if "extract.extract_sublevels.convs.0.0.conv.weight" in sd:
            model = FILMNet()
            model.load_state_dict(sd)
            return model

        # Try RIFE (needs key remapping for raw checkpoints)
        sd = comfy.utils.state_dict_prefix_replace(sd, {"module.": "", "flownet.": ""})
        key_map = {}
        for k in sd:
            for i in range(5):
                if k.startswith(f"block{i}."):
                    key_map[k] = f"blocks.{i}.{k[len(f'block{i}.'):]}"
        if key_map:
            sd = {key_map.get(k, k): v for k, v in sd.items()}
        sd = {k: v for k, v in sd.items() if not k.startswith(("teacher.", "caltime."))}

        try:
            head_ch, channels = detect_rife_config(sd)
        except (KeyError, ValueError):
            raise ValueError("Unrecognized frame interpolation model format")
        model = IFNet(head_ch=head_ch, channels=channels)
        model.load_state_dict(sd)
        return model