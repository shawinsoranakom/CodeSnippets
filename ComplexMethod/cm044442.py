def _get_net(self) -> nn.ModuleList:
        """Load the linear network, set the weights

        Returns
        -------
        The Linear network for the given trunk network
        """
        net_info = _LINEAR[self._net_name]
        layers: list[nn.Module] = []
        for in_channels in net_info.outputs:
            assert isinstance(in_channels, int)
            conv = nn.Conv2d(in_channels, 1, 1, stride=1, padding=0, bias=False)
            if self._use_dropout:
                layers.append(nn.Sequential(nn.Dropout(), conv))
            else:
                layers.append(conv)

        net = nn.ModuleList(layers)

        if self._load_weights:
            weights_path = GetModel(net_info.model_name, net_info.model_id).model_path
            assert isinstance(weights_path, str)
            weights = torch.load(weights_path)
            state = net.state_dict()
            assert len(weights) == len(state)
            for key, val in zip(list(state), weights.values()):
                state[key] = val

            net.load_state_dict(state)

        if self._eval_mode:
            net.eval()
        return net