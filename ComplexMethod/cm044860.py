def __init__(self, model_path, config_path, device, is_half):
        self.device = device
        self.is_half = is_half
        self.model_type = None
        self.config = None

        # get model_type, first try:
        if "bs_roformer" in model_path.lower() or "bsroformer" in model_path.lower():
            self.model_type = "bs_roformer"
        elif "mel_band_roformer" in model_path.lower() or "melbandroformer" in model_path.lower():
            self.model_type = "mel_band_roformer"

        if not os.path.exists(config_path):
            if self.model_type is None:
                # if model_type is still None, raise an error
                raise ValueError(
                    "Error: Unknown model type. If you are using a model without a configuration file, Ensure that your model name includes 'bs_roformer', 'bsroformer', 'mel_band_roformer', or 'melbandroformer'. Otherwise, you can manually place the model configuration file into 'tools/uvr5/uvr5w_weights' and ensure that the configuration file is named as '<model_name>.yaml' then try it again."
                )
            self.config = self.get_default_config()
        else:
            # if there is a configuration file
            self.config = self.get_config(config_path)
            if self.model_type is None:
                # if model_type is still None, second try, get model_type from the configuration file
                if "freqs_per_bands" in self.config["model"]:
                    # if freqs_per_bands in config, it's a bs_roformer model
                    self.model_type = "bs_roformer"
                else:
                    # else it's a mel_band_roformer model
                    self.model_type = "mel_band_roformer"

        print("Detected model type: {}".format(self.model_type))
        model = self.get_model_from_config()
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)

        if is_half == False:
            self.model = model.to(device)
        else:
            self.model = model.half().to(device)