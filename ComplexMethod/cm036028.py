def step(self, batch: any, batch_idx: BatchIndex):
        """
        ### Training or validation step with Gauss-Newton-Bartlett (GNB) Hessian diagonal estimator
        """

        # Set training/eval mode
        self.model.train(self.mode.is_train)

        # Move data to the device
        data, target = batch[0].to(self.device), batch[1].to(self.device)

        # Estimate the Hessian diagonal every $k$ steps
        if isinstance(self.optimizer, Sophia) and self.mode.is_train and batch_idx.idx % self.hess_interval == 0:
            # Get model outputs
            output, *_ = self.model(data)

            # Create a categorical distribution from logits
            samp_dist = torch.distributions.Categorical(logits=output)
            # Sample $\hat{y}$
            y_sample = samp_dist.sample()

            # Calculate and log loss
            loss = self.loss_func(output, y_sample)
            tracker.add("loss.hess.", loss)

            # Calculate gradients
            loss.backward()
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=self.grad_norm_clip)
            # Update EMA Hessian diagonal
            #
            # \begin{align}
            # \hat{h}_t &= B \cdot \nabla_\theta \hat{L} (\theta) \odot \nabla_\theta \hat{L} (\theta) \\
            # h_t &= \beta_2 h_{t-k} + (1 - \beta_2) \hat{h}_t
            # \end{align}
            self.optimizer.update_hessian(data.numel())
            # Clear the gradients
            self.optimizer.zero_grad()
        else:
            # Move data to the device
            data, target = batch[0].to(self.device), batch[1].to(self.device)

            # Update global step (number of tokens processed) when in training mode
            if self.mode.is_train:
                tracker.add_global_step(data.shape[0] * data.shape[1])

            # Get model outputs.
            # It's returning a tuple for states when using RNNs.
            # This is not implemented yet. 😜
            output, *_ = self.model(data)

            # Calculate and log loss
            loss = self.loss_func(output, target)
            tracker.add("loss.", loss)

            # Calculate and log accuracy
            self.accuracy(output, target)
            self.accuracy.track()

            self.other_metrics(output, target)

            # Train the model
            if self.mode.is_train:
                # Calculate gradients
                loss.backward()
                # Clip gradients
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=self.grad_norm_clip)
                # Take optimizer step
                self.optimizer.step()
                # Log the model parameters and gradients on last batch of every epoch
                if batch_idx.is_last and self.is_log_model_params_grads:
                    tracker.add('model', self.model)
                # Clear the gradients
                self.optimizer.zero_grad()

            # Save the tracked metrics
            tracker.save()