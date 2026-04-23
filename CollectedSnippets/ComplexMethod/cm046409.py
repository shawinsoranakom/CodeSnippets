def forward(self, x):
        """Forward pass through the model.

        This method performs the forward pass through the model, handling the dependencies between layers and saving
        intermediate outputs.

        Args:
            x (torch.Tensor): The input tensor to the model.

        Returns:
            (torch.Tensor): The output tensor from the model.
        """
        y = []  # outputs
        for m in self.model:
            if m.f != -1:  # if not from previous layer
                # from earlier layers
                x = y[m.f] if isinstance(m.f, int) else [x if j == -1 else y[j] for j in m.f]
            if isinstance(m, Detect):
                m._inference = types.MethodType(_inference, m)  # bind method to Detect
                m.anchors, m.strides = (
                    x.transpose(0, 1)
                    for x in make_anchors(
                        torch.cat([s / m.stride.unsqueeze(-1) for s in self.imgsz], dim=1), m.stride, 0.5
                    )
                )
            if type(m) is Pose:
                m.forward = types.MethodType(pose_forward, m)  # bind method to Pose
            if type(m) is Segment:
                m.forward = types.MethodType(segment_forward, m)  # bind method to Segment
            x = m(x)  # run
            y.append(x)  # save output
        return x