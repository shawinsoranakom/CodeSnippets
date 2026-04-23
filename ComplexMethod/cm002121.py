def test_load_backbone_in_new_model(self):
        """
        Tests that new model can be created, with its weights instantiated and pretrained backbone weights loaded.
        """

        # Inherit from PreTrainedModel to ensure that the weights are initialized
        class NewModel(BertPreTrainedModel):
            def __init__(self, config):
                super().__init__(config)
                self.backbone = load_backbone(config)
                self.layer_0 = torch.nn.Linear(config.hidden_size, config.hidden_size)
                self.layer_1 = torch.nn.Linear(config.hidden_size, config.hidden_size)

        def get_equal_not_equal_weights(model_0, model_1):
            equal_weights = []
            not_equal_weights = []
            for (k0, v0), (k1, v1) in zip(model_0.named_parameters(), model_1.named_parameters()):
                self.assertEqual(k0, k1)
                weights_are_equal = torch.allclose(v0, v1)
                if weights_are_equal:
                    equal_weights.append(k0)
                else:
                    not_equal_weights.append(k0)
            return equal_weights, not_equal_weights

        config = MaskFormerConfig(use_pretrained_backbone=False, backbone="microsoft/resnet-18")
        model_0 = NewModel(config)
        model_1 = NewModel(config)
        equal_weights, not_equal_weights = get_equal_not_equal_weights(model_0, model_1)

        # Norm layers are always initialized with the same weights
        equal_weights = [w for w in equal_weights if "normalization" not in w]
        self.assertEqual(len(equal_weights), 0)
        self.assertEqual(len(not_equal_weights), 24)

        # Now we create a new model with backbone weights that are pretrained
        config.use_pretrained_backbone = True
        model_0 = NewModel(config)
        model_1 = NewModel(config)
        equal_weights, not_equal_weights = get_equal_not_equal_weights(model_0, model_1)

        # Norm layers are always initialized with the same weights
        equal_weights = [w for w in equal_weights if "normalization" not in w]
        self.assertEqual(len(equal_weights), 20)
        # Linear layers are still initialized randomly
        self.assertEqual(len(not_equal_weights), 4)

        # Check loading in timm backbone
        config = DetrConfig(use_pretrained_backbone=False, backbone="resnet18", use_timm_backbone=True)
        model_0 = NewModel(config)
        model_1 = NewModel(config)
        equal_weights, not_equal_weights = get_equal_not_equal_weights(model_0, model_1)

        # Norm layers are always initialized with the same weights
        equal_weights = [w for w in equal_weights if "bn" not in w and "downsample.1" not in w]
        self.assertEqual(len(equal_weights), 0)
        self.assertEqual(len(not_equal_weights), 24)

        # Now we create a new model with backbone weights that are pretrained
        config.use_pretrained_backbone = True
        model_0 = NewModel(config)
        model_1 = NewModel(config)
        equal_weights, not_equal_weights = get_equal_not_equal_weights(model_0, model_1)

        # Norm layers are always initialized with the same weights
        equal_weights = [w for w in equal_weights if "bn" not in w and "downsample.1" not in w]
        self.assertEqual(len(equal_weights), 20)
        # Linear layers are still initialized randomly
        self.assertEqual(len(not_equal_weights), 4)