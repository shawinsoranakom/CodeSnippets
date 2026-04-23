def init_from_ckpt(self, path, ignore_keys=None, only_model=False):
        ignore_keys = ignore_keys or []

        sd = torch.load(path, map_location="cpu")
        if "state_dict" in list(sd.keys()):
            sd = sd["state_dict"]
        keys = list(sd.keys())

        # Our model adds additional channels to the first layer to condition on an input image.
        # For the first layer, copy existing channel weights and initialize new channel weights to zero.
        input_keys = [
            "model.diffusion_model.input_blocks.0.0.weight",
            "model_ema.diffusion_modelinput_blocks00weight",
        ]

        self_sd = self.state_dict()
        for input_key in input_keys:
            if input_key not in sd or input_key not in self_sd:
                continue

            input_weight = self_sd[input_key]

            if input_weight.size() != sd[input_key].size():
                print(f"Manual init: {input_key}")
                input_weight.zero_()
                input_weight[:, :4, :, :].copy_(sd[input_key])
                ignore_keys.append(input_key)

        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print(f"Deleting key {k} from state_dict.")
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False) if not only_model else self.model.load_state_dict(
            sd, strict=False)
        print(f"Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys")
        if missing:
            print(f"Missing Keys: {missing}")
        if unexpected:
            print(f"Unexpected Keys: {unexpected}")