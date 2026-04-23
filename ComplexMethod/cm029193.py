async def execute_skill(
		self, skill_id: str, parameters: dict[str, Any] | BaseModel, cookies: list[Cookie]
	) -> ExecuteSkillResponse:
		"""Execute a skill with the provided parameters. Auto-initializes if not already initialized.

		Parameters are validated against the skill's Pydantic schema before execution.

		Args:
			skill_id: The UUID of the skill to execute
			parameters: Either a dictionary or BaseModel instance matching the skill's parameter schema

		Returns:
			ExecuteSkillResponse with execution results

		Raises:
			ValueError: If skill not found in cache or parameter validation fails
			Exception: If API call fails
		"""
		# Auto-initialize if needed
		if not self._initialized:
			await self.async_init()

		assert self._client is not None, 'Client not initialized'

		# Check if skill exists in cache
		skill = await self.get_skill(skill_id)
		if skill is None:
			raise ValueError(f'Skill {skill_id} not found in cache. Available skills: {list(self._skills.keys())}')

		# Extract cookie parameters from the skill
		cookie_params = [p for p in skill.parameters if p.type == 'cookie']

		# Build a dict of cookies from the provided cookie list
		cookie_dict: dict[str, str] = {cookie['name']: cookie['value'] for cookie in cookies}

		# Check for missing required cookies and fill cookie values
		if cookie_params:
			for cookie_param in cookie_params:
				is_required = cookie_param.required if cookie_param.required is not None else True

				if is_required and cookie_param.name not in cookie_dict:
					# Required cookie is missing - raise exception with description
					raise MissingCookieException(
						cookie_name=cookie_param.name, cookie_description=cookie_param.description or 'No description provided'
					)

			# Fill in cookie values into parameters
			# Convert parameters to dict first if it's a BaseModel
			if isinstance(parameters, BaseModel):
				params_dict = parameters.model_dump()
			else:
				params_dict = dict(parameters)

			# Add cookie values to parameters
			for cookie_param in cookie_params:
				if cookie_param.name in cookie_dict:
					params_dict[cookie_param.name] = cookie_dict[cookie_param.name]

			# Replace parameters with the updated dict
			parameters = params_dict

		# Get the skill's pydantic model for parameter validation
		ParameterModel = skill.parameters_pydantic(exclude_cookies=False)

		# Validate and convert parameters to dict
		validated_params_dict: dict[str, Any]

		try:
			if isinstance(parameters, BaseModel):
				# Already a pydantic model - validate it matches the skill's schema
				# by converting to dict and re-validating with the skill's model
				params_dict = parameters.model_dump()
				validated_model = ParameterModel(**params_dict)
				validated_params_dict = validated_model.model_dump()
			else:
				# Dict provided - validate with the skill's pydantic model
				validated_model = ParameterModel(**parameters)
				validated_params_dict = validated_model.model_dump()

		except ValidationError as e:
			# Pydantic validation failed
			error_msg = f'Parameter validation failed for skill {skill.title}:\n'
			for error in e.errors():
				field = '.'.join(str(x) for x in error['loc'])
				error_msg += f'  - {field}: {error["msg"]}\n'
			raise ValueError(error_msg) from e
		except Exception as e:
			raise ValueError(f'Failed to validate parameters for skill {skill.title}: {type(e).__name__}: {e}') from e

		# Execute skill via API
		try:
			logger.info(f'Executing skill: {skill.title} ({skill_id})')
			result: ExecuteSkillResponse = await self._client.skills.execute_skill(
				skill_id=skill_id, parameters=validated_params_dict
			)

			if result.success:
				logger.info(f'Skill {skill.title} executed successfully (latency: {result.latency_ms}ms)')
			else:
				logger.error(f'Skill {skill.title} execution failed: {result.error}')

			return result

		except Exception as e:
			logger.error(f'Error executing skill {skill_id}: {type(e).__name__}: {e}')
			# Return error response
			return ExecuteSkillResponse(
				success=False,
				result=None,
				error=f'Failed to execute skill: {type(e).__name__}: {str(e)}',
				stderr=None,
				latencyMs=None,
			)