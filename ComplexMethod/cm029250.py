def get_user_message(self, use_vision: bool = True) -> UserMessage:
		"""Get complete state as a single cached message"""
		# Don't pass screenshot to model if page is a new tab page, step is 0, and there's only one tab
		if (
			is_new_tab_page(self.browser_state.url)
			and self.step_info is not None
			and self.step_info.step_number == 0
			and len(self.browser_state.tabs) == 1
		):
			use_vision = False

		# Build complete state description
		state_description = (
			'<agent_history>\n'
			+ (self.agent_history_description.strip('\n') if self.agent_history_description else '')
			+ '\n</agent_history>\n\n'
		)
		state_description += '<agent_state>\n' + self._get_agent_state_description().strip('\n') + '\n</agent_state>\n'
		state_description += '<browser_state>\n' + self._get_browser_state_description().strip('\n') + '\n</browser_state>\n'
		# Only add read_state if it has content
		read_state_description = self.read_state_description.strip('\n').strip() if self.read_state_description else ''
		if read_state_description:
			state_description += '<read_state>\n' + read_state_description + '\n</read_state>\n'

		if self.page_filtered_actions:
			state_description += '<page_specific_actions>\n'
			state_description += self.page_filtered_actions + '\n'
			state_description += '</page_specific_actions>\n'

		# Add unavailable skills information if any
		if self.unavailable_skills_info:
			state_description += '\n' + self.unavailable_skills_info + '\n'

		# Sanitize surrogates from all text content
		state_description = sanitize_surrogates(state_description)

		# Check if we have images to include (from read_file action)
		has_images = bool(self.read_state_images)

		if (use_vision is True and self.screenshots) or has_images:
			# Start with text description
			content_parts: list[ContentPartTextParam | ContentPartImageParam] = [ContentPartTextParam(text=state_description)]

			# Add sample images
			content_parts.extend(self.sample_images)

			# Add screenshots with labels
			for i, screenshot in enumerate(self.screenshots):
				if i == len(self.screenshots) - 1:
					label = 'Current screenshot:'
				else:
					# Use simple, accurate labeling since we don't have actual step timing info
					label = 'Previous screenshot:'

				# Add label as text content
				content_parts.append(ContentPartTextParam(text=label))

				# Resize screenshot if llm_screenshot_size is configured
				processed_screenshot = self._resize_screenshot(screenshot)

				# Add the screenshot
				content_parts.append(
					ContentPartImageParam(
						image_url=ImageURL(
							url=f'data:image/png;base64,{processed_screenshot}',
							media_type='image/png',
							detail=self.vision_detail_level,
						),
					)
				)

			# Add read_state images (from read_file action) before screenshots
			for img_data in self.read_state_images:
				img_name = img_data.get('name', 'unknown')
				img_base64 = img_data.get('data', '')

				if not img_base64:
					continue

				# Detect image format from name
				if img_name.lower().endswith('.png'):
					media_type = 'image/png'
				else:
					media_type = 'image/jpeg'

				# Add label
				content_parts.append(ContentPartTextParam(text=f'Image from file: {img_name}'))

				# Add the image
				content_parts.append(
					ContentPartImageParam(
						image_url=ImageURL(
							url=f'data:{media_type};base64,{img_base64}',
							media_type=media_type,
							detail=self.vision_detail_level,
						),
					)
				)

			return UserMessage(content=content_parts, cache=True)

		return UserMessage(content=state_description, cache=True)