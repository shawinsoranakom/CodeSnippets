def forward(self, inputs: list[torch.Tensor]) -> list[torch.Tensor]:
        """Forward pass through the HR Module

        Parameters
        ----------
        inputs
            Input to the HR Module

        Returns
        -------
        Output from the HR Module
        """
        x = inputs
        if self.num_branches == 1:
            return [self.branches[0](x[0])]
        assert self.fuse_layers is not None

        for i in range(self.num_branches):
            x[i] = self.branches[i](x[i])

        x_fuse = []
        for i, fuse_layer in enumerate(T.cast(list[nn.ModuleList], self.fuse_layers)):
            y = x[0] if i == 0 else fuse_layer[0](x[0])
            for j in range(1, self.num_branches):
                if i == j:
                    y = y + x[j]
                elif j > i:
                    y = y + F.interpolate(fuse_layer[j](x[j]),
                                          size=[x[i].shape[2], x[i].shape[3]],
                                          mode="bilinear")
                else:
                    y = y + fuse_layer[j](x[j])
            x_fuse.append(self.relu(y))
        return x_fuse