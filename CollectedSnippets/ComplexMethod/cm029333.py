def _on_response_received(self, params: ResponseReceivedEvent, session_id: str | None) -> None:
		try:
			request_id = params.get('requestId') if hasattr(params, 'get') else getattr(params, 'requestId', None)
			if not request_id or request_id not in self._entries:
				return
			response = params.get('response', {}) if hasattr(params, 'get') else getattr(params, 'response', {})
			entry = self._entries[request_id]
			entry.status = response.get('status') if isinstance(response, dict) else getattr(response, 'status', None)
			entry.status_text = (
				response.get('statusText') if isinstance(response, dict) else getattr(response, 'statusText', None)
			)

			# Extract Content-Length for compression calculation (before converting headers)
			headers_raw = response.get('headers') if isinstance(response, dict) else getattr(response, 'headers', None)
			if headers_raw:
				if isinstance(headers_raw, dict):
					cl_str = headers_raw.get('content-length') or headers_raw.get('Content-Length')
				elif isinstance(headers_raw, list):
					cl_header = next(
						(h for h in headers_raw if isinstance(h, dict) and h.get('name', '').lower() == 'content-length'), None
					)
					cl_str = cl_header.get('value') if cl_header else None
				else:
					cl_str = None
				if cl_str:
					try:
						entry.content_length = int(cl_str)
					except Exception:
						pass

			# Convert headers to plain dict, handling various formats
			if headers_raw is None:
				entry.response_headers = {}
			elif isinstance(headers_raw, dict):
				entry.response_headers = {k.lower(): str(v) for k, v in headers_raw.items()}
			elif isinstance(headers_raw, list):
				entry.response_headers = {
					h.get('name', '').lower(): str(h.get('value') or '') for h in headers_raw if isinstance(h, dict)
				}
			else:
				# Handle Headers type or other formats - convert to dict
				try:
					headers_dict = dict(headers_raw) if hasattr(headers_raw, '__iter__') else {}
					entry.response_headers = {k.lower(): str(v) for k, v in headers_dict.items()}
				except Exception:
					entry.response_headers = {}

			entry.mime_type = response.get('mimeType') if isinstance(response, dict) else getattr(response, 'mimeType', None)
			entry.ts_response = params.get('timestamp') if hasattr(params, 'get') else getattr(params, 'timestamp', None)

			protocol_raw = response.get('protocol') if isinstance(response, dict) else getattr(response, 'protocol', None)
			if protocol_raw:
				protocol_lower = str(protocol_raw).lower()
				if protocol_lower == 'h2' or protocol_lower.startswith('http/2'):
					entry.protocol = 'HTTP/2.0'
				elif protocol_lower.startswith('http/1.1'):
					entry.protocol = 'HTTP/1.1'
				elif protocol_lower.startswith('http/1.0'):
					entry.protocol = 'HTTP/1.0'
				else:
					entry.protocol = str(protocol_raw).upper()

			entry.server_ip_address = (
				response.get('remoteIPAddress') if isinstance(response, dict) else getattr(response, 'remoteIPAddress', None)
			)
			server_port_raw = response.get('remotePort') if isinstance(response, dict) else getattr(response, 'remotePort', None)
			if server_port_raw is not None:
				try:
					entry.server_port = int(server_port_raw)
				except (ValueError, TypeError):
					pass

			# Extract security details (TLS info)
			security_details_raw = (
				response.get('securityDetails') if isinstance(response, dict) else getattr(response, 'securityDetails', None)
			)
			if security_details_raw:
				try:
					entry.security_details = dict(security_details_raw)
				except Exception:
					pass
		except Exception as e:
			self.logger.debug(f'responseReceived handling error: {e}')