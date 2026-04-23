async def async_init(self) -> None:
		"""Async initialization to fetch all skills at once

		This should be called after __init__ to fetch and cache all skills.
		Fetches all available skills in one API call and filters based on skill_ids.
		"""
		if self._initialized:
			logger.debug('SkillService already initialized')
			return

		# Create the SDK client
		self._client = AsyncBrowserUse(api_key=self.api_key)

		try:
			# Fetch skills from API
			logger.info('Fetching skills from Browser Use API...')
			use_wildcard = '*' in self.skill_ids
			page_size = 100
			requested_ids: set[str] = set() if use_wildcard else {s for s in self.skill_ids if s != '*'}

			if use_wildcard:
				# Wildcard: fetch only first page (max 100 skills) to avoid LLM tool overload
				skills_response: SkillListResponse = await self._client.skills.list_skills(
					page_size=page_size,
					page_number=1,
					is_enabled=True,
				)
				all_items = list(skills_response.items)

				if len(all_items) >= page_size:
					logger.warning(
						f'Wildcard "*" limited to first {page_size} skills. '
						f'Specify explicit skill IDs if you need specific skills beyond this limit.'
					)

				logger.debug(f'Fetched {len(all_items)} skills (wildcard mode, single page)')
			else:
				# Explicit IDs: paginate until all requested IDs found
				all_items = []
				page = 1
				max_pages = 5  # Safety limit

				while page <= max_pages:
					skills_response = await self._client.skills.list_skills(
						page_size=page_size,
						page_number=page,
						is_enabled=True,
					)
					all_items.extend(skills_response.items)

					# Check if we've found all requested skills
					found_ids = {str(s.id) for s in all_items if str(s.id) in requested_ids}
					if found_ids == requested_ids:
						break

					# Stop if we got fewer items than page_size (last page)
					if len(skills_response.items) < page_size:
						break
					page += 1

				if page > max_pages:
					logger.warning(f'Reached pagination limit ({max_pages} pages) before finding all requested skills')

				logger.debug(f'Fetched {len(all_items)} skills across {page} page(s)')

			# Filter to only finished skills (is_enabled already filtered by API)
			all_available_skills = [skill for skill in all_items if skill.status == 'finished']

			logger.info(f'Found {len(all_available_skills)} available skills from API')

			# Determine which skills to load
			if use_wildcard:
				logger.info('Wildcard "*" detected, loading first 100 skills')
				skills_to_load = all_available_skills
			else:
				# Load only the requested skill IDs
				skills_to_load = [skill for skill in all_available_skills if str(skill.id) in requested_ids]

				# Warn about any requested skills that weren't found
				found_ids = {str(skill.id) for skill in skills_to_load}
				missing_ids = requested_ids - found_ids
				if missing_ids:
					logger.warning(f'Requested skills not found or not available: {missing_ids}')

			# Convert SDK SkillResponse objects to our Skill models and cache them
			for skill_response in skills_to_load:
				try:
					skill = Skill.from_skill_response(skill_response)
					self._skills[skill.id] = skill
					logger.debug(f'Cached skill: {skill.title} ({skill.id})')
				except Exception as e:
					logger.error(f'Failed to convert skill {skill_response.id}: {type(e).__name__}: {e}')

			logger.info(f'Successfully loaded {len(self._skills)} skills')
			self._initialized = True

		except Exception as e:
			logger.error(f'Error during skill initialization: {type(e).__name__}: {e}')
			self._initialized = True  # Mark as initialized even on failure to avoid retry loops
			raise