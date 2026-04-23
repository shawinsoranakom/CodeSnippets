def forward(self, body_feats):
        laterals = []
        num_levels = len(body_feats)

        for i in range(num_levels):
            laterals.append(self.lateral_convs[i](body_feats[i]))

        for i in range(1, num_levels):
            lvl = num_levels - i
            upsample = F.interpolate(
                laterals[lvl],
                scale_factor=2.0,
                mode="nearest",
            )
            laterals[lvl - 1] += upsample

        fpn_output = []
        for lvl in range(num_levels):
            fpn_output.append(self.fpn_convs[lvl](laterals[lvl]))

        if self.extra_stage > 0:
            # use max pool to get more levels on top of outputs (Faster R-CNN, Mask R-CNN)
            if not self.has_extra_convs:
                assert (
                    self.extra_stage == 1
                ), "extra_stage should be 1 if FPN has not extra convs"
                fpn_output.append(F.max_pool2d(fpn_output[-1], 1, stride=2))
            # add extra conv levels for RetinaNet(use_c5)/FCOS(use_p5)
            else:
                if self.use_c5:
                    extra_source = body_feats[-1]
                else:
                    extra_source = fpn_output[-1]
                fpn_output.append(self.fpn_convs[num_levels](extra_source))

                for i in range(1, self.extra_stage):
                    if self.relu_before_extra_convs:
                        fpn_output.append(
                            self.fpn_convs[num_levels + i](F.relu(fpn_output[-1]))
                        )
                    else:
                        fpn_output.append(
                            self.fpn_convs[num_levels + i](fpn_output[-1])
                        )
        return fpn_output