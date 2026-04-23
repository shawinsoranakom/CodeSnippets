def sample_extra(conditioning, unconditional_conditioning, seeds, subseeds, subseed_strength, prompts):
            lat = (p.init_latent.cpu().numpy() * 10).astype(int)

            same_params = self.cache is not None and self.cache.cfg_scale == cfg and self.cache.steps == st \
                                and self.cache.original_prompt == original_prompt \
                                and self.cache.original_negative_prompt == original_negative_prompt \
                                and self.cache.sigma_adjustment == sigma_adjustment
            same_everything = same_params and self.cache.latent.shape == lat.shape and np.abs(self.cache.latent-lat).sum() < 100

            if same_everything:
                rec_noise = self.cache.noise
            else:
                shared.state.job_count += 1
                cond = p.sd_model.get_learned_conditioning(p.batch_size * [original_prompt])
                uncond = p.sd_model.get_learned_conditioning(p.batch_size * [original_negative_prompt])
                if sigma_adjustment:
                    rec_noise = find_noise_for_image_sigma_adjustment(p, cond, uncond, cfg, st)
                else:
                    rec_noise = find_noise_for_image(p, cond, uncond, cfg, st)
                self.cache = Cached(rec_noise, cfg, st, lat, original_prompt, original_negative_prompt, sigma_adjustment)

            rand_noise = processing.create_random_tensors(p.init_latent.shape[1:], seeds=seeds, subseeds=subseeds, subseed_strength=p.subseed_strength, seed_resize_from_h=p.seed_resize_from_h, seed_resize_from_w=p.seed_resize_from_w, p=p)

            combined_noise = ((1 - randomness) * rec_noise + randomness * rand_noise) / ((randomness**2 + (1-randomness)**2) ** 0.5)

            sampler = sd_samplers.create_sampler(p.sampler_name, p.sd_model)

            sigmas = sampler.model_wrap.get_sigmas(p.steps)

            noise_dt = combined_noise - (p.init_latent / sigmas[0])

            p.seed = p.seed + 1

            return sampler.sample_img2img(p, p.init_latent, noise_dt, conditioning, unconditional_conditioning, image_conditioning=p.image_conditioning)