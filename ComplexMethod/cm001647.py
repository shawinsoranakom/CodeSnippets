def setup_prompts(self):
        super().setup_prompts()

        if not self.enable_hr:
            return

        if self.hr_prompt == '':
            self.hr_prompt = self.prompt

        if self.hr_negative_prompt == '':
            self.hr_negative_prompt = self.negative_prompt

        if isinstance(self.hr_prompt, list):
            self.all_hr_prompts = self.hr_prompt
        else:
            self.all_hr_prompts = self.batch_size * self.n_iter * [self.hr_prompt]

        if isinstance(self.hr_negative_prompt, list):
            self.all_hr_negative_prompts = self.hr_negative_prompt
        else:
            self.all_hr_negative_prompts = self.batch_size * self.n_iter * [self.hr_negative_prompt]

        self.all_hr_prompts = [shared.prompt_styles.apply_styles_to_prompt(x, self.styles) for x in self.all_hr_prompts]
        self.all_hr_negative_prompts = [shared.prompt_styles.apply_negative_styles_to_prompt(x, self.styles) for x in self.all_hr_negative_prompts]