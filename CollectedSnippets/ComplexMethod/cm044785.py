def forward(self, x: Tensor) -> Tensor:
        if torch.jit.is_scripting() or not x.requires_grad or torch.jit.is_tracing():
            return _no_op(x)

        count = self.cpu_count
        self.cpu_count += 1

        if random.random() < 0.01:
            # Occasionally sync self.cpu_count with self.count.
            # count affects the decay of 'prob'.  don't do this on every iter,
            # because syncing with the GPU is slow.
            self.cpu_count = max(self.cpu_count, self.count.item())
            self.count.fill_(self.cpu_count)

        # the prob of doing some work exponentially decreases from 0.5 till it hits
        # a floor at min_prob (==0.1, by default)
        prob = max(self.min_prob, 0.5 ** (1 + (count / 4000.0)))

        if random.random() < prob:
            sign_gain_factor = 0.5
            if self.min_positive != 0.0 or self.max_positive != 1.0:
                sign_factor = _compute_sign_factor(
                    x,
                    self.channel_dim,
                    self.min_positive,
                    self.max_positive,
                    gain_factor=self.sign_gain_factor / prob,
                    max_factor=self.max_factor,
                )
            else:
                sign_factor = None

            scale_factor = _compute_scale_factor(
                x.detach(),
                self.channel_dim,
                min_abs=self.min_abs,
                max_abs=self.max_abs,
                gain_factor=self.scale_gain_factor / prob,
                max_factor=self.max_factor,
            )
            return ActivationBalancerFunction.apply(
                x,
                scale_factor,
                sign_factor,
                self.channel_dim,
            )
        else:
            return _no_op(x)