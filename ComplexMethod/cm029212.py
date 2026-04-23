async def _get_unavailable_skills_info(self) -> str:
		"""Get information about skills that are unavailable due to missing cookies

		Returns:
			Formatted string describing unavailable skills and how to make them available
		"""
		if not self.skill_service:
			return ''

		try:
			# Get all skills
			skills = await self.skill_service.get_all_skills()
			if not skills:
				return ''

			# Get current cookies
			current_cookies = await self.browser_session.cookies()
			cookie_dict = {cookie['name']: cookie['value'] for cookie in current_cookies}

			# Check each skill for missing required cookies
			unavailable_skills: list[dict[str, Any]] = []

			for skill in skills:
				# Get cookie parameters for this skill
				cookie_params = [p for p in skill.parameters if p.type == 'cookie']

				if not cookie_params:
					# No cookies needed, skip
					continue

				# Check for missing required cookies
				missing_cookies: list[dict[str, str]] = []
				for cookie_param in cookie_params:
					is_required = cookie_param.required if cookie_param.required is not None else True

					if is_required and cookie_param.name not in cookie_dict:
						missing_cookies.append(
							{'name': cookie_param.name, 'description': cookie_param.description or 'No description provided'}
						)

				if missing_cookies:
					unavailable_skills.append(
						{
							'id': skill.id,
							'title': skill.title,
							'description': skill.description,
							'missing_cookies': missing_cookies,
						}
					)

			if not unavailable_skills:
				return ''

			# Format the unavailable skills info with slugs
			lines = ['Unavailable Skills (missing required cookies):']
			for skill_info in unavailable_skills:
				# Get the full skill object to use the slug helper
				skill_obj = next((s for s in skills if s.id == skill_info['id']), None)
				slug = self._get_skill_slug(skill_obj, skills) if skill_obj else skill_info['title']
				title = skill_info['title']

				lines.append(f'\n  • {slug} ("{title}")')
				lines.append(f'    Description: {skill_info["description"]}')
				lines.append('    Missing cookies:')
				for cookie in skill_info['missing_cookies']:
					lines.append(f'      - {cookie["name"]}: {cookie["description"]}')

			return '\n'.join(lines)

		except Exception as e:
			self.logger.error(f'Error getting unavailable skills info: {type(e).__name__}: {e}')
			return ''