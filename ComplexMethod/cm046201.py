def _prepare_backbone_features(self, backbone_out, batch=1):
        """Prepare and flatten visual features from the image backbone output for further processing."""
        if batch > 1:  # expand features if there's more than one prompt
            backbone_out = {
                **backbone_out,
                "backbone_fpn": [feat.expand(batch, -1, -1, -1) for feat in backbone_out["backbone_fpn"]],
                "vision_pos_enc": [pos.expand(batch, -1, -1, -1) for pos in backbone_out["vision_pos_enc"]],
            }
        assert len(backbone_out["backbone_fpn"]) == len(backbone_out["vision_pos_enc"])
        assert len(backbone_out["backbone_fpn"]) >= self.num_feature_levels

        feature_maps = backbone_out["backbone_fpn"][-self.num_feature_levels :]
        vision_pos_embeds = backbone_out["vision_pos_enc"][-self.num_feature_levels :]

        feat_sizes = [(x.shape[-2], x.shape[-1]) for x in vision_pos_embeds]
        # flatten NxCxHxW to HWxNxC
        vision_feats = [x.flatten(2).permute(2, 0, 1) for x in feature_maps]
        vision_pos_embeds = [x.flatten(2).permute(2, 0, 1) for x in vision_pos_embeds]
        return backbone_out, vision_feats, vision_pos_embeds, feat_sizes