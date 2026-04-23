def _load_prompt_template(self) -> None:
		"""Load the prompt template from the markdown file."""
		try:
			# Choose the appropriate template based on model type and mode
			# Browser-use models use simplified prompts optimized for fine-tuned models
			if self.is_browser_use_model:
				if self.flash_mode:
					template_filename = 'system_prompt_browser_use_flash.md'
				elif self.use_thinking:
					template_filename = 'system_prompt_browser_use.md'
				else:
					template_filename = 'system_prompt_browser_use_no_thinking.md'
			# Anthropic 4.5 models (Opus 4.5, Haiku 4.5) need 4096+ token prompts for caching
			elif self.is_anthropic_4_5 and self.flash_mode:
				template_filename = 'system_prompt_anthropic_flash.md'
			elif self.flash_mode and self.is_anthropic:
				template_filename = 'system_prompt_flash_anthropic.md'
			elif self.flash_mode:
				template_filename = 'system_prompt_flash.md'
			elif self.use_thinking:
				template_filename = 'system_prompt.md'
			else:
				template_filename = 'system_prompt_no_thinking.md'

			# This works both in development and when installed as a package
			with (
				importlib.resources.files('browser_use.agent.system_prompts')
				.joinpath(template_filename)
				.open('r', encoding='utf-8') as f
			):
				self.prompt_template = f.read()
		except Exception as e:
			raise RuntimeError(f'Failed to load system prompt template: {e}')