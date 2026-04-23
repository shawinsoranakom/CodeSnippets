def __init__(self, config):
        nn.Module.__init__()

        self.config = config

        backbone = load_backbone(config)
        self.intermediate_channel_sizes = backbone.channels

        # replace batch norm by frozen batch norm
        with torch.no_grad():
            replace_batch_norm(backbone)

        # We used to load with timm library directly instead of the AutoBackbone API
        # so we need to unwrap the `backbone._backbone` module to load weights without mismatch
        is_timm_model = False
        if hasattr(backbone, "_backbone"):
            backbone = backbone._backbone
            is_timm_model = True
        self.model = backbone

        backbone_model_type = config.backbone_config.model_type
        if "resnet" in backbone_model_type:
            for name, parameter in self.model.named_parameters():
                if is_timm_model:
                    if "layer2" not in name and "layer3" not in name and "layer4" not in name:
                        parameter.requires_grad_(False)
                else:
                    if "stage.1" not in name and "stage.2" not in name and "stage.3" not in name:
                        parameter.requires_grad_(False)