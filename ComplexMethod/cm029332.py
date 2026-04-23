def _on_request_will_be_sent(self, params: RequestWillBeSentEvent, session_id: str | None) -> None:
		try:
			req = params.get('request', {}) if hasattr(params, 'get') else getattr(params, 'request', {})
			url = req.get('url') if isinstance(req, dict) else getattr(req, 'url', None)
			if not _is_https(url):
				return  # HTTPS-only requirement (only HTTPS requests are recorded for now)

			request_id = params.get('requestId') if hasattr(params, 'get') else getattr(params, 'requestId', None)
			if not request_id:
				return

			entry = self._entries.setdefault(request_id, _HarEntryBuilder(request_id=request_id))
			entry.url = url
			entry.method = req.get('method') if isinstance(req, dict) else getattr(req, 'method', None)
			entry.post_data = req.get('postData') if isinstance(req, dict) else getattr(req, 'postData', None)

			# Convert headers to plain dict, handling various formats
			headers_raw = req.get('headers') if isinstance(req, dict) else getattr(req, 'headers', None)
			if headers_raw is None:
				entry.request_headers = {}
			elif isinstance(headers_raw, dict):
				entry.request_headers = {k.lower(): str(v) for k, v in headers_raw.items()}
			elif isinstance(headers_raw, list):
				entry.request_headers = {
					h.get('name', '').lower(): str(h.get('value') or '') for h in headers_raw if isinstance(h, dict)
				}
			else:
				# Handle Headers type or other formats - convert to dict
				try:
					headers_dict = dict(headers_raw) if hasattr(headers_raw, '__iter__') else {}
					entry.request_headers = {k.lower(): str(v) for k, v in headers_dict.items()}
				except Exception:
					entry.request_headers = {}

			entry.frame_id = params.get('frameId') if hasattr(params, 'get') else getattr(params, 'frameId', None)
			entry.document_url = (
				params.get('documentURL')
				if hasattr(params, 'get')
				else getattr(params, 'documentURL', None) or entry.document_url
			)

			# Timing anchors
			entry.ts_request = params.get('timestamp') if hasattr(params, 'get') else getattr(params, 'timestamp', None)
			entry.wall_time_request = params.get('wallTime') if hasattr(params, 'get') else getattr(params, 'wallTime', None)

			# Track top-level navigations for page context
			req_type = params.get('type') if hasattr(params, 'get') else getattr(params, 'type', None)
			is_same_doc = (
				params.get('isSameDocument', False) if hasattr(params, 'get') else getattr(params, 'isSameDocument', False)
			)
			if req_type == 'Document' and not is_same_doc:
				# best-effort: consider as navigation
				if entry.frame_id and url:
					if entry.frame_id not in self._top_level_pages:
						self._top_level_pages[entry.frame_id] = {
							'url': str(url),
							'title': str(url),  # Default to URL, will be updated from DOM
							'startedDateTime': entry.wall_time_request,
							'monotonic_start': entry.ts_request,  # Track monotonic start time for timing calculations
							'onContentLoad': -1,
							'onLoad': -1,
						}
					else:
						# Update startedDateTime and monotonic_start if this is earlier
						page_info = self._top_level_pages[entry.frame_id]
						if entry.wall_time_request and (
							page_info['startedDateTime'] is None or entry.wall_time_request < page_info['startedDateTime']
						):
							page_info['startedDateTime'] = entry.wall_time_request
							page_info['monotonic_start'] = entry.ts_request
		except Exception as e:
			self.logger.debug(f'requestWillBeSent handling error: {e}')