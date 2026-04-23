def sample(self, conditioning, unconditional_conditioning, seeds, subseeds, subseed_strength, prompts):
        self.sampler = sd_samplers.create_sampler(self.sampler_name, self.sd_model)

        if self.firstpass_image is not None and self.enable_hr:
            # here we don't need to generate image, we just take self.firstpass_image and prepare it for hires fix

            if self.latent_scale_mode is None:
                image = np.array(self.firstpass_image).astype(np.float32) / 255.0 * 2.0 - 1.0
                image = np.moveaxis(image, 2, 0)

                samples = None
                decoded_samples = torch.asarray(np.expand_dims(image, 0))

            else:
                image = np.array(self.firstpass_image).astype(np.float32) / 255.0
                image = np.moveaxis(image, 2, 0)
                image = torch.from_numpy(np.expand_dims(image, axis=0))
                image = image.to(shared.device, dtype=devices.dtype_vae)

                if opts.sd_vae_encode_method != 'Full':
                    self.extra_generation_params['VAE Encoder'] = opts.sd_vae_encode_method

                samples = images_tensor_to_samples(image, approximation_indexes.get(opts.sd_vae_encode_method), self.sd_model)
                decoded_samples = None
                devices.torch_gc()

        else:
            # here we generate an image normally

            x = self.rng.next()
            if self.scripts is not None:
                self.scripts.process_before_every_sampling(
                    p=self,
                    x=x,
                    noise=x,
                    c=conditioning,
                    uc=unconditional_conditioning
                )

            samples = self.sampler.sample(self, x, conditioning, unconditional_conditioning, image_conditioning=self.txt2img_image_conditioning(x))
            del x

            if not self.enable_hr:
                return samples

            devices.torch_gc()

            if self.latent_scale_mode is None:
                decoded_samples = torch.stack(decode_latent_batch(self.sd_model, samples, target_device=devices.cpu, check_for_nans=True)).to(dtype=torch.float32)
            else:
                decoded_samples = None

        with sd_models.SkipWritingToConfig():
            sd_models.reload_model_weights(info=self.hr_checkpoint_info)

        return self.sample_hr_pass(samples, decoded_samples, seeds, subseeds, subseed_strength, prompts)