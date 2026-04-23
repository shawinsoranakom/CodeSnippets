async def skill_handler(params: BaseModel) -> ActionResult:
					"""Execute a specific skill"""
					assert self.skill_service is not None, 'SkillService not initialized'

					# Convert parameters to dict
					if isinstance(params, BaseModel):
						skill_params = params.model_dump()
					elif isinstance(params, dict):
						skill_params = params
					else:
						return ActionResult(extracted_content=None, error=f'Invalid parameters type: {type(params)}')

					# Get cookies from browser
					_cookies = await self.browser_session.cookies()

					try:
						result = await self.skill_service.execute_skill(
							skill_id=skill_id, parameters=skill_params, cookies=_cookies
						)

						if result.success:
							return ActionResult(
								extracted_content=str(result.result) if result.result else None,
								error=None,
							)
						else:
							return ActionResult(extracted_content=None, error=result.error or 'Skill execution failed')
					except Exception as e:
						# Check if it's a MissingCookieException
						if type(e).__name__ == 'MissingCookieException':
							# Format: "Missing cookies (name): description"
							cookie_name = getattr(e, 'cookie_name', 'unknown')
							cookie_description = getattr(e, 'cookie_description', str(e))
							error_msg = f'Missing cookies ({cookie_name}): {cookie_description}'
							return ActionResult(extracted_content=None, error=error_msg)
						return ActionResult(extracted_content=None, error=f'Skill execution error: {type(e).__name__}: {e}')