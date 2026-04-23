async def get_recent_emails(params: GetRecentEmailsParams) -> ActionResult:
		"""Get recent emails from the last 5 minutes with full content"""
		try:
			if _gmail_service is None:
				raise RuntimeError('Gmail service not initialized')

			# Ensure authentication
			if not _gmail_service.is_authenticated():
				logger.info('📧 Gmail not authenticated, attempting authentication...')
				authenticated = await _gmail_service.authenticate()
				if not authenticated:
					return ActionResult(
						extracted_content='Failed to authenticate with Gmail. Please ensure Gmail credentials are set up properly.',
						long_term_memory='Gmail authentication failed',
					)

			# Use specified max_results (1-50, default 10), last 5 minutes
			max_results = params.max_results
			time_filter = '5m'

			# Build query with time filter and optional user query
			query_parts = [f'newer_than:{time_filter}']
			if params.keyword.strip():
				query_parts.append(params.keyword.strip())

			query = ' '.join(query_parts)
			logger.info(f'🔍 Gmail search query: {query}')

			# Get emails
			emails = await _gmail_service.get_recent_emails(max_results=max_results, query=query, time_filter=time_filter)

			if not emails:
				query_info = f" matching '{params.keyword}'" if params.keyword.strip() else ''
				memory = f'No recent emails found from last {time_filter}{query_info}'
				return ActionResult(
					extracted_content=memory,
					long_term_memory=memory,
				)

			# Format with full email content for large display
			content = f'Found {len(emails)} recent email{"s" if len(emails) > 1 else ""} from the last {time_filter}:\n\n'

			for i, email in enumerate(emails, 1):
				content += f'Email {i}:\n'
				content += f'From: {email["from"]}\n'
				content += f'Subject: {email["subject"]}\n'
				content += f'Date: {email["date"]}\n'
				content += f'Content:\n{email["body"]}\n'
				content += '-' * 50 + '\n\n'

			logger.info(f'📧 Retrieved {len(emails)} recent emails')
			return ActionResult(
				extracted_content=content,
				include_extracted_content_only_once=True,
				long_term_memory=f'Retrieved {len(emails)} recent emails from last {time_filter} for query {query}.',
			)

		except Exception as e:
			logger.error(f'Error getting recent emails: {e}')
			return ActionResult(
				error=f'Error getting recent emails: {str(e)}',
				long_term_memory='Failed to get recent emails due to error',
			)