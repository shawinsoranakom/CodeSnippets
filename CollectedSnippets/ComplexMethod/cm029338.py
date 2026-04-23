async def _write_har(self) -> None:
		# Filter by mode and HTTPS already respected at collection time
		entries = [e for e in self._entries.values() if self._include_entry(e)]

		har_entries = []
		sidecar_dir: Path | None = None
		if self._content_mode == 'attach':
			sidecar_dir = self._har_dir / f'{self._har_path.stem}_har_parts'
			sidecar_dir.mkdir(parents=True, exist_ok=True)

		for e in entries:
			content_obj: dict = {'mimeType': e.mime_type or ''}

			# Get body data, preferring response_body over encoded_data
			if e.response_body is not None:
				body_data = e.response_body
			else:
				body_data = e.encoded_data

			# Defensive conversion: ensure body_data is always bytes
			if isinstance(body_data, str):
				body_bytes = body_data.encode('utf-8', errors='replace')
			elif isinstance(body_data, bytearray):
				body_bytes = bytes(body_data)
			elif isinstance(body_data, bytes):
				body_bytes = body_data
			else:
				# Fallback: try to convert to bytes
				try:
					body_bytes = bytes(body_data) if body_data else b''
				except (TypeError, ValueError):
					body_bytes = b''

			content_size = len(body_bytes)

			# Calculate compression (bytes saved by compression)
			compression = 0
			if e.content_length is not None and e.encoded_data_length is not None:
				compression = max(0, e.content_length - e.encoded_data_length)

			if self._content_mode == 'embed' and content_size > 0:
				# Prefer plain text; fallback to base64 only if decoding fails
				try:
					text_decoded = body_bytes.decode('utf-8')
					content_obj['text'] = text_decoded
					content_obj['size'] = content_size
					content_obj['compression'] = compression
				except UnicodeDecodeError:
					content_obj['text'] = base64.b64encode(body_bytes).decode('ascii')
					content_obj['encoding'] = 'base64'
					content_obj['size'] = content_size
					content_obj['compression'] = compression
			elif self._content_mode == 'attach' and content_size > 0 and sidecar_dir is not None:
				filename = _generate_har_filename(body_bytes, e.mime_type)
				(sidecar_dir / filename).write_bytes(body_bytes)
				content_obj['_file'] = filename
				content_obj['size'] = content_size
				content_obj['compression'] = compression
			else:
				# omit or empty
				content_obj['size'] = content_size
				if content_size > 0:
					content_obj['compression'] = compression

			started_date_time, total_time_ms, timings = self._compute_timings(e)
			req_headers_list = [{'name': k, 'value': str(v)} for k, v in (e.request_headers or {}).items()]
			resp_headers_list = [{'name': k, 'value': str(v)} for k, v in (e.response_headers or {}).items()]
			request_headers_size = self._calc_headers_size(e.method or 'GET', e.url or '', req_headers_list)
			response_headers_size = self._calc_headers_size(None, None, resp_headers_list)
			request_body_size = self._calc_request_body_size(e)
			request_post_data = None
			if e.post_data and self._content_mode != 'omit':
				if self._content_mode == 'embed':
					request_post_data = {'mimeType': e.request_headers.get('content-type', ''), 'text': e.post_data}
				elif self._content_mode == 'attach' and sidecar_dir is not None:
					post_data_bytes = e.post_data.encode('utf-8')
					req_mime_type = e.request_headers.get('content-type', 'text/plain')
					req_filename = _generate_har_filename(post_data_bytes, req_mime_type)
					(sidecar_dir / req_filename).write_bytes(post_data_bytes)
					request_post_data = {
						'mimeType': req_mime_type,
						'_file': req_filename,
					}

			http_version = e.protocol if e.protocol else 'HTTP/1.1'

			response_body_size = e.transfer_size
			if response_body_size is None:
				response_body_size = e.encoded_data_length
			if response_body_size is None:
				response_body_size = content_size if content_size > 0 else -1

			entry_dict = {
				'startedDateTime': started_date_time,
				'time': total_time_ms,
				'request': {
					'method': e.method or 'GET',
					'url': e.url or '',
					'httpVersion': http_version,
					'headers': req_headers_list,
					'queryString': [],
					'cookies': [],
					'headersSize': request_headers_size,
					'bodySize': request_body_size,
					'postData': request_post_data,
				},
				'response': {
					'status': e.status or 0,
					'statusText': e.status_text or '',
					'httpVersion': http_version,
					'headers': resp_headers_list,
					'cookies': [],
					'content': content_obj,
					'redirectURL': '',
					'headersSize': response_headers_size,
					'bodySize': response_body_size,
				},
				'cache': {},
				'timings': timings,
				'pageref': self._page_ref_for_entry(e),
			}

			# Add security/TLS details if available
			if e.server_ip_address:
				entry_dict['serverIPAddress'] = e.server_ip_address
			if e.server_port is not None:
				entry_dict['_serverPort'] = e.server_port
			if e.security_details:
				# Filter to match Playwright's minimal security details set
				security_filtered = {}
				if 'protocol' in e.security_details:
					security_filtered['protocol'] = e.security_details['protocol']
				if 'subjectName' in e.security_details:
					security_filtered['subjectName'] = e.security_details['subjectName']
				if 'issuer' in e.security_details:
					security_filtered['issuer'] = e.security_details['issuer']
				if 'validFrom' in e.security_details:
					security_filtered['validFrom'] = e.security_details['validFrom']
				if 'validTo' in e.security_details:
					security_filtered['validTo'] = e.security_details['validTo']
				if security_filtered:
					entry_dict['_securityDetails'] = security_filtered
			if e.transfer_size is not None:
				entry_dict['response']['_transferSize'] = e.transfer_size

			har_entries.append(entry_dict)

		# Try to include our library version in creator
		try:
			bu_version = importlib_metadata.version('browser-use')
		except Exception:
			# Fallback when running from source without installed package metadata
			bu_version = 'dev'

		har_obj = {
			'log': {
				'version': '1.2',
				'creator': {'name': 'browser-use', 'version': bu_version},
				'browser': {'name': self._browser_name, 'version': self._browser_version},
				'pages': [
					{
						'id': f'page@{pid}',  # Use Playwright format: "page@{frame_id}"
						'title': page_info.get('title', page_info.get('url', '')),
						'startedDateTime': self._format_page_started_datetime(page_info.get('startedDateTime')),
						'pageTimings': (
							(lambda _ocl, _ol: ({k: v for k, v in (('onContentLoad', _ocl), ('onLoad', _ol)) if v is not None}))(
								(page_info.get('onContentLoad') if page_info.get('onContentLoad', -1) >= 0 else None),
								(page_info.get('onLoad') if page_info.get('onLoad', -1) >= 0 else None),
							)
						),
					}
					for pid, page_info in self._top_level_pages.items()
				],
				'entries': har_entries,
			}
		}

		tmp_path = self._har_path.with_suffix(self._har_path.suffix + '.tmp')
		# Write as bytes explicitly to avoid any text/binary mode confusion in different environments
		tmp_path.write_bytes(json.dumps(har_obj, indent=2, ensure_ascii=False).encode('utf-8'))
		tmp_path.replace(self._har_path)