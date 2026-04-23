async def get_recent_emails(self, max_results: int = 10, query: str = '', time_filter: str = '1h') -> list[dict[str, Any]]:
		"""
		Get recent emails with optional query filter
		Args:
		    max_results: Maximum number of emails to fetch
		    query: Gmail search query (e.g., 'from:noreply@example.com')
		    time_filter: Time filter (e.g., '5m', '1h', '1d')
		Returns:
		    List of email dictionaries with parsed content
		"""
		if not self.is_authenticated():
			logger.error('❌ Gmail service not authenticated. Call authenticate() first.')
			return []

		try:
			# Add time filter to query if provided
			if time_filter and 'newer_than:' not in query:
				query = f'newer_than:{time_filter} {query}'.strip()

			logger.info(f'📧 Fetching {max_results} recent emails...')
			if query:
				logger.debug(f'🔍 Query: {query}')

			# Get message list
			assert self.service is not None
			results = self.service.users().messages().list(userId='me', maxResults=max_results, q=query).execute()

			messages = results.get('messages', [])
			if not messages:
				logger.info('📭 No messages found')
				return []

			logger.info(f'📨 Found {len(messages)} messages, fetching details...')

			# Get full message details
			emails = []
			for i, message in enumerate(messages, 1):
				logger.debug(f'📖 Reading email {i}/{len(messages)}...')

				full_message = self.service.users().messages().get(userId='me', id=message['id'], format='full').execute()

				email_data = self._parse_email(full_message)
				emails.append(email_data)

			return emails

		except HttpError as error:
			logger.error(f'❌ Gmail API error: {error}')
			return []
		except Exception as e:
			logger.error(f'❌ Unexpected error fetching emails: {e}')
			return []