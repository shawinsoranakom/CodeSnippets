def _init_weights(self, m):
        if isinstance(m, paddle.nn.Linear):
            trunc_normal_init(m.weight, std=0.02)
            if m.bias is not None:
                constant_init(m.bias, value=0.0)
        elif isinstance(m, paddle.nn.Embedding):
            trunc_normal_init(m.weight, std=0.02)
            if m._padding_idx is not None:
                m.weight.data[m._padding_idx].zero_()
        elif isinstance(m, paddle.nn.Conv2D):
            kaiming_normal_init(m.weight, fan_in=None, nonlinearity="relu")
            if m.bias is not None:
                constant_init(m.bias, value=0.0)
        elif isinstance(
            m, (paddle.nn.LayerNorm, paddle.nn.BatchNorm2D, paddle.nn.GroupNorm)
        ):
            constant_init(m.weight, value=1.0)
            constant_init(m.bias, value=0.0)