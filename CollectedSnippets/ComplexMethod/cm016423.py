def test_longcat_comfyui_detected_as_longcat(self):
        sd = _make_longcat_comfyui_sd()
        unet_config = detect_unet_config(sd, "")
        assert unet_config is not None
        assert unet_config["image_model"] == "flux"
        assert unet_config["context_in_dim"] == 3584
        assert unet_config["vec_in_dim"] is None
        assert unet_config["guidance_embed"] is False
        assert unet_config["txt_ids_dims"] == [1, 2]

        model_config = model_config_from_unet_config(unet_config, sd)
        assert model_config is not None
        assert type(model_config).__name__ == "LongCatImage"