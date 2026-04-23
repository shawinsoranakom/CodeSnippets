def train_epoch(self):
        # Set model for train
        self.model.train()

        iterators = self.get_iterators()
        for split_name, sample in monit.mix(1024, *iterators):
            if split_name == 'train':
                # Set gradients to zero
                self.optimizer.zero_grad()
                tracker.add_global_step()

            with torch.set_grad_enabled(split_name == 'train'):
                if self.is_amp:
                    # Forward pass
                    with amp.autocast():
                        loss, output, target = self.get_loss(sample, split_name)
                else:
                    loss, output, target = self.get_loss(sample, split_name)

                # Get predictions
                pred = output.argmax(dim=-1)
                # Calculate accuracy
                accuracy = pred.eq(target).sum().item() / (target != -100).sum()

                tracker.add({f'loss.{split_name}': loss, f'acc.{split_name}': accuracy * 100})

            if split_name == 'train':
                if self.scaler is not None:
                    # Backward pass
                    loss = self.scaler.scale(loss)
                    # tracker.add({'loss.scaled': loss})

                with monit.section('Backward pass'):
                    loss.backward()

                # Optimize
                with monit.section('Optimize'):
                    if self.scaler is None:
                        self.optimizer.step()
                    else:
                        self.scaler.unscale_(self.optimizer)
                        if self.grad_norm is not None:
                            torch.nn.utils.clip_grad_norm_(get_trainable_params(self.model), self.grad_norm)
                        self.scaler.step(self.optimizer)
                        self.scaler.update()

            tracker.save()