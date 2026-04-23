def step(self, idx: int):
        """
        ### Training Step
        """

        # Train the discriminator
        with monit.section('Discriminator'):
            # Reset gradients
            self.discriminator_optimizer.zero_grad()

            # Accumulate gradients for `gradient_accumulate_steps`
            for i in range(self.gradient_accumulate_steps):
                # Sample images from generator
                generated_images, _ = self.generate_images(self.batch_size)
                # Discriminator classification for generated images
                fake_output = self.discriminator(generated_images.detach())

                # Get real images from the data loader
                real_images = next(self.loader).to(self.device)
                # We need to calculate gradients w.r.t. real images for gradient penalty
                if (idx + 1) % self.lazy_gradient_penalty_interval == 0:
                    real_images.requires_grad_()
                # Discriminator classification for real images
                real_output = self.discriminator(real_images)

                # Get discriminator loss
                real_loss, fake_loss = self.discriminator_loss(real_output, fake_output)
                disc_loss = real_loss + fake_loss

                # Add gradient penalty
                if (idx + 1) % self.lazy_gradient_penalty_interval == 0:
                    # Calculate and log gradient penalty
                    gp = self.gradient_penalty(real_images, real_output)
                    tracker.add('loss.gp', gp)
                    # Multiply by coefficient and add gradient penalty
                    disc_loss = disc_loss + 0.5 * self.gradient_penalty_coefficient * gp * self.lazy_gradient_penalty_interval

                # Compute gradients
                disc_loss.backward()

                # Log discriminator loss
                tracker.add('loss.discriminator', disc_loss)

            if (idx + 1) % self.log_generated_interval == 0:
                # Log discriminator model parameters occasionally
                tracker.add('discriminator', self.discriminator)

            # Clip gradients for stabilization
            torch.nn.utils.clip_grad_norm_(self.discriminator.parameters(), max_norm=1.0)
            # Take optimizer step
            self.discriminator_optimizer.step()

        # Train the generator
        with monit.section('Generator'):
            # Reset gradients
            self.generator_optimizer.zero_grad()
            self.mapping_network_optimizer.zero_grad()

            # Accumulate gradients for `gradient_accumulate_steps`
            for i in range(self.gradient_accumulate_steps):
                # Sample images from generator
                generated_images, w = self.generate_images(self.batch_size)
                # Discriminator classification for generated images
                fake_output = self.discriminator(generated_images)

                # Get generator loss
                gen_loss = self.generator_loss(fake_output)

                # Add path length penalty
                if idx > self.lazy_path_penalty_after and (idx + 1) % self.lazy_path_penalty_interval == 0:
                    # Calculate path length penalty
                    plp = self.path_length_penalty(w, generated_images)
                    # Ignore if `nan`
                    if not torch.isnan(plp):
                        tracker.add('loss.plp', plp)
                        gen_loss = gen_loss + plp

                # Calculate gradients
                gen_loss.backward()

                # Log generator loss
                tracker.add('loss.generator', gen_loss)

            if (idx + 1) % self.log_generated_interval == 0:
                # Log discriminator model parameters occasionally
                tracker.add('generator', self.generator)
                tracker.add('mapping_network', self.mapping_network)

            # Clip gradients for stabilization
            torch.nn.utils.clip_grad_norm_(self.generator.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(self.mapping_network.parameters(), max_norm=1.0)

            # Take optimizer step
            self.generator_optimizer.step()
            self.mapping_network_optimizer.step()

        # Log generated images
        if (idx + 1) % self.log_generated_interval == 0:
            tracker.add('generated', torch.cat([generated_images[:6], real_images[:3]], dim=0))
        # Save model checkpoints
        if (idx + 1) % self.save_checkpoint_interval == 0:
            # Save checkpoint
            pass

        # Flush tracker
        tracker.save()