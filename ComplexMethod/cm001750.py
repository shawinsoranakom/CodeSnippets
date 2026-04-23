def test_num_layers_is_small(self):
        # TODO (if possible): Avoid exceptional cases, especially for `OwlViT`.
        # ⛔ DO NOT edit this list (unless there is really nothing to tweak in the model tester class and approved by the reviewer) ⛔!
        exceptional_num_hidden_layers = {
            # TODO: There might be some way to fix
            "FunnelModelTest": 5,
            "FunnelBaseModelTest": 4,
            "GroupViTVisionModelTest": 12,
            "OwlViTModelTest": 12,
            "OwlViTTextModelTest": 12,
            "OwlViTForObjectDetectionTest": 12,
            "Owlv2ModelTest": 12,
            "Owlv2TextModelTest": 12,
            "Owlv2ForObjectDetectionTest": 12,
            "Qwen2_5OmniThinkerForConditionalGenerationModelTest": 4,
            "Qwen3OmniMoeThinkerForConditionalGenerationModelTest": 4,
            "SamHQModelTest": 12,
            "Swin2SRModelTest": 3,
            "XLNetModelTest": 3,
            "DPTModelTest": 4,  # `test_modeling_dpt_hybrid.py`: not able to get it work after change `num_hidden_layers` and `neck_hidden_sizes`
            # Nothing we can't do
            "Gemma3nTextModelTest": 4,  # need to test KV shared layer for both types: `full_attention` and `sliding_attention`
            "Gemma3nVision2TextModelTest": 4,  # need to test KV shared layer for both types: `full_attention` and `sliding_attention`
            "BeitModelTest": 4,  # BeitForSemanticSegmentation requires config.out_indices to be a list of 4 integers
            "ZambaModelTest": 5,  # The minimum number to test beyond the initial ["mamba", "mamba", "hybrid"] in `ZambaConfig._layers_block_type`
        }
        target_num_hidden_layers = exceptional_num_hidden_layers.get(type(self).__name__, 2)

        if hasattr(self.model_tester, "num_hidden_layers") and isinstance(self.model_tester.num_hidden_layers, int):
            assert self.model_tester.num_hidden_layers <= target_num_hidden_layers

        if hasattr(self.model_tester, "vision_config") and "num_hidden_layers" in self.model_tester.vision_config:
            if isinstance(self.model_tester.vision_config, dict):
                assert self.model_tester.vision_config["num_hidden_layers"] <= target_num_hidden_layers
            else:
                assert self.model_tester.vision_config.num_hidden_layers <= target_num_hidden_layers
        if hasattr(self.model_tester, "text_config") and "num_hidden_layers" in self.model_tester.text_config:
            if isinstance(self.model_tester.text_config, dict):
                assert self.model_tester.text_config["num_hidden_layers"] <= target_num_hidden_layers
            else:
                assert self.model_tester.text_config.num_hidden_layers <= target_num_hidden_layers