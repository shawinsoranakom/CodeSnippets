def test_extract_content_pattern_registration(self):
		"""Test that the extract_content pattern with mixed params registers correctly"""
		registry = Registry()

		# This is the problematic pattern: positional arg, then special args, then kwargs with defaults
		@registry.action('Extract content from page')
		async def extract_content(
			goal: str,
			page_extraction_llm,
			include_links: bool = False,
		):
			return ActionResult(extracted_content=f'Goal: {goal}, include_links: {include_links}')

		# Verify registration
		assert 'extract_content' in registry.registry.actions
		action = registry.registry.actions['extract_content']

		# Check that the param model only includes user-facing params
		model_fields = action.param_model.model_fields
		assert 'goal' in model_fields
		assert 'include_links' in model_fields
		assert model_fields['include_links'].default is False

		# Special params should NOT be in the model
		assert 'page' not in model_fields
		assert 'page_extraction_llm' not in model_fields

		# Verify the action was properly registered
		assert action.name == 'extract_content'
		assert action.description == 'Extract content from page'