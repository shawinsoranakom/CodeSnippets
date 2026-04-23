def forward(self, backbone_stage_feature_maps: list[torch.Tensor], **kwargs) -> torch.Tensor:
        channel_adjusted = []
        for i, feature_map in enumerate(backbone_stage_feature_maps):
            hidden_states = self.input_channel_adjustment_convolution[i](feature_map)
            channel_adjusted.append(hidden_states)

        top_down = [None] * self.num_backbone_stages
        top_down[3] = channel_adjusted[3]
        for i in range(self.num_backbone_stages - 2, -1, -1):
            top_down[i] = channel_adjusted[i] + F.interpolate(
                top_down[i + 1], scale_factor=2, mode=self.interpolate_mode
            )

        projected = []
        for i in range(self.num_backbone_stages):
            hidden_states = top_down[i] if i < self.num_backbone_stages - 1 else channel_adjusted[-1]
            hidden_states = self.input_feature_projection_convolution[i](hidden_states)
            projected.append(hidden_states)

        bottom_up = [None] * self.num_backbone_stages
        bottom_up[0] = projected[0]
        for i in range(1, self.num_backbone_stages):
            bottom_up[i] = projected[i] + self.path_aggregation_head_convolution[i - 1](bottom_up[i - 1])

        lateral_refined = []
        for i in range(self.num_backbone_stages):
            hidden_states = projected[0] if i == 0 else bottom_up[i]
            hidden_states = self.path_aggregation_lateral_convolution[i](hidden_states)
            lateral_refined.append(hidden_states)

        intraclass_refined = [block(feature) for block, feature in zip(self.intraclass_blocks, lateral_refined)]

        upsampled = []
        for feature, scale_factor in zip(intraclass_refined, self.scale_factor_list):
            if scale_factor > 1:
                hidden_states = F.interpolate(feature, scale_factor=scale_factor, mode=self.interpolate_mode)
            else:
                hidden_states = feature
            upsampled.append(hidden_states)

        upsampled = [
            F.interpolate(feature, scale_factor=scale_factor, mode=self.interpolate_mode)
            if scale_factor > 1
            else feature
            for feature, scale_factor in zip(intraclass_refined, self.scale_factor_list)
        ]

        return torch.cat(upsampled[::-1], dim=1)