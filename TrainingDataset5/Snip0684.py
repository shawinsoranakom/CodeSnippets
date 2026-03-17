 def load_model_from_config(self, half_attention):
        global cached_ldsr_model

        if shared.opts.ldsr_cached and cached_ldsr_model is not None:
            print("Loading model from cache")
            model: torch.nn.Module = cached_ldsr_model
        else:
            print(f"Loading model from {self.modelPath}")
            _, extension = os.path.splitext(self.modelPath)
            if extension.lower() == ".safetensors":
                pl_sd = safetensors.torch.load_file(self.modelPath, device="cpu")
            else:
                pl_sd = torch.load(self.modelPath, map_location="cpu")
            sd = pl_sd["state_dict"] if "state_dict" in pl_sd else pl_sd
            config = OmegaConf.load(self.yamlPath)
            config.model.target = "ldm.models.diffusion.ddpm.LatentDiffusionV1"
            model: torch.nn.Module = instantiate_from_config(config.model)
            model.load_state_dict(sd, strict=False)
            model = model.to(shared.device)
            if half_attention:
                model = model.half()
            if shared.cmd_opts.opt_channelslast:
                model = model.to(memory_format=torch.channels_last)

            sd_hijack.model_hijack.hijack(model) # apply optimization
            model.eval()

            if shared.opts.ldsr_cached:
                cached_ldsr_model = model

        return {"model": model}
