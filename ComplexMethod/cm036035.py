def forward(self, x: torch.Tensor,
                state: Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]] = None):
        """
        * `x` has shape `[n_steps, batch_size, input_size]` and
        * `state` is a tuple of $h, c, \hat{h}, \hat{c}$.
         $h, c$ have shape `[batch_size, hidden_size]` and
         $\hat{h}, \hat{c}$ have shape `[batch_size, hyper_size]`.
        """
        n_steps, batch_size = x.shape[:2]

        # Initialize the state with zeros if `None`
        if state is None:
            h = [x.new_zeros(batch_size, self.hidden_size) for _ in range(self.n_layers)]
            c = [x.new_zeros(batch_size, self.hidden_size) for _ in range(self.n_layers)]
            h_hat = [x.new_zeros(batch_size, self.hyper_size) for _ in range(self.n_layers)]
            c_hat = [x.new_zeros(batch_size, self.hyper_size) for _ in range(self.n_layers)]
        #
        else:
            (h, c, h_hat, c_hat) = state
            # Reverse stack the tensors to get the states of each layer
            #
            # 📝 You can just work with the tensor itself but this is easier to debug
            h, c = list(torch.unbind(h)), list(torch.unbind(c))
            h_hat, c_hat = list(torch.unbind(h_hat)), list(torch.unbind(c_hat))

        # Collect the outputs of the final layer at each step
        out = []
        for t in range(n_steps):
            # Input to the first layer is the input itself
            inp = x[t]
            # Loop through the layers
            for layer in range(self.n_layers):
                # Get the state of the layer
                h[layer], c[layer], h_hat[layer], c_hat[layer] = \
                    self.cells[layer](inp, h[layer], c[layer], h_hat[layer], c_hat[layer])
                # Input to the next layer is the state of this layer
                inp = h[layer]
            # Collect the output $h$ of the final layer
            out.append(h[-1])

        # Stack the outputs and states
        out = torch.stack(out)
        h = torch.stack(h)
        c = torch.stack(c)
        h_hat = torch.stack(h_hat)
        c_hat = torch.stack(c_hat)

        #
        return out, (h, c, h_hat, c_hat)