async def _retry_with_browser_use_agent(
		self,
		task: str,
		max_steps: int = 100,
		model: str | None = None,
		allowed_domains: list[str] | None = None,
		use_vision: bool = True,
	) -> str:
		"""Run an autonomous agent task."""
		logger.debug(f'Running agent task: {task}')

		# Get LLM config
		llm_config = get_default_llm(self.config)

		# Get LLM provider
		model_provider = llm_config.get('model_provider') or os.getenv('MODEL_PROVIDER')

		# Get Bedrock-specific config
		if model_provider and model_provider.lower() == 'bedrock':
			llm_model = llm_config.get('model') or os.getenv('MODEL') or 'us.anthropic.claude-sonnet-4-20250514-v1:0'
			aws_region = llm_config.get('region') or os.getenv('REGION')
			if not aws_region:
				aws_region = 'us-east-1'
			aws_sso_auth = llm_config.get('aws_sso_auth', False)
			llm = ChatAWSBedrock(
				model=llm_model,  # or any Bedrock model
				aws_region=aws_region,
				aws_sso_auth=aws_sso_auth,
			)
		else:
			api_key = llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
			if not api_key:
				return 'Error: OPENAI_API_KEY not set in config or environment'

			# Use explicit model from tool call, otherwise fall back to configured default
			llm_model = model or llm_config.get('model', 'gpt-4o')

			base_url = llm_config.get('base_url', None)
			kwargs = {}
			if base_url:
				kwargs['base_url'] = base_url
			llm = ChatOpenAI(
				model=llm_model,
				api_key=api_key,
				temperature=llm_config.get('temperature', 0.7),
				**kwargs,
			)

		# Get profile config and merge with tool parameters
		profile_config = get_default_profile(self.config)

		# Override allowed_domains if provided in tool call
		if allowed_domains is not None:
			profile_config['allowed_domains'] = allowed_domains

		# Create browser profile using config
		profile = BrowserProfile(**profile_config)

		# Create and run agent
		agent = Agent(
			task=task,
			llm=llm,
			browser_profile=profile,
			use_vision=use_vision,
		)

		try:
			history = await agent.run(max_steps=max_steps)

			# Format results
			results = []
			results.append(f'Task completed in {len(history.history)} steps')
			results.append(f'Success: {history.is_successful()}')

			# Get final result if available
			final_result = history.final_result()
			if final_result:
				results.append(f'\nFinal result:\n{final_result}')

			# Include any errors
			errors = history.errors()
			if errors:
				results.append(f'\nErrors encountered:\n{json.dumps(errors, indent=2)}')

			# Include URLs visited
			urls = history.urls()
			if urls:
				# Filter out None values and convert to strings
				valid_urls = [str(url) for url in urls if url is not None]
				if valid_urls:
					results.append(f'\nURLs visited: {", ".join(valid_urls)}')

			return '\n'.join(results)

		except Exception as e:
			logger.error(f'Agent task failed: {e}', exc_info=True)
			return f'Agent task failed: {str(e)}'
		finally:
			# Clean up
			await agent.close()