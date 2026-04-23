def init(self, all_prompts, all_seeds, all_subseeds):
        if self.enable_hr:
            self.extra_generation_params["Denoising strength"] = self.denoising_strength

            if self.hr_checkpoint_name and self.hr_checkpoint_name != 'Use same checkpoint':
                self.hr_checkpoint_info = sd_models.get_closet_checkpoint_match(self.hr_checkpoint_name)

                if self.hr_checkpoint_info is None:
                    raise Exception(f'Could not find checkpoint with name {self.hr_checkpoint_name}')

                self.extra_generation_params["Hires checkpoint"] = self.hr_checkpoint_info.short_title

            if self.hr_sampler_name is not None and self.hr_sampler_name != self.sampler_name:
                self.extra_generation_params["Hires sampler"] = self.hr_sampler_name

            def get_hr_prompt(p, index, prompt_text, **kwargs):
                hr_prompt = p.all_hr_prompts[index]
                return hr_prompt if hr_prompt != prompt_text else None

            def get_hr_negative_prompt(p, index, negative_prompt, **kwargs):
                hr_negative_prompt = p.all_hr_negative_prompts[index]
                return hr_negative_prompt if hr_negative_prompt != negative_prompt else None

            self.extra_generation_params["Hires prompt"] = get_hr_prompt
            self.extra_generation_params["Hires negative prompt"] = get_hr_negative_prompt

            self.extra_generation_params["Hires schedule type"] = None  # to be set in sd_samplers_kdiffusion.py

            if self.hr_scheduler is None:
                self.hr_scheduler = self.scheduler

            self.latent_scale_mode = shared.latent_upscale_modes.get(self.hr_upscaler, None) if self.hr_upscaler is not None else shared.latent_upscale_modes.get(shared.latent_upscale_default_mode, "nearest")
            if self.enable_hr and self.latent_scale_mode is None:
                if not any(x.name == self.hr_upscaler for x in shared.sd_upscalers):
                    raise Exception(f"could not find upscaler named {self.hr_upscaler}")

            self.calculate_target_resolution()

            if not state.processing_has_refined_job_count:
                if state.job_count == -1:
                    state.job_count = self.n_iter
                if getattr(self, 'txt2img_upscale', False):
                    total_steps = (self.hr_second_pass_steps or self.steps) * state.job_count
                else:
                    total_steps = (self.steps + (self.hr_second_pass_steps or self.steps)) * state.job_count
                shared.total_tqdm.updateTotal(total_steps)
                state.job_count = state.job_count * 2
                state.processing_has_refined_job_count = True

            if self.hr_second_pass_steps:
                self.extra_generation_params["Hires steps"] = self.hr_second_pass_steps

            if self.hr_upscaler is not None:
                self.extra_generation_params["Hires upscaler"] = self.hr_upscaler