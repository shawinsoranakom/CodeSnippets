def _on_loading_finished(self, params: LoadingFinishedEvent, session_id: str | None) -> None:
		try:
			request_id = params.get('requestId') if hasattr(params, 'get') else getattr(params, 'requestId', None)
			if not request_id or request_id not in self._entries:
				return
			entry = self._entries[request_id]
			entry.ts_finished = params.get('timestamp')
			# Fetch response body via CDP as dataReceived may be incomplete
			import asyncio as _asyncio

			async def _fetch_body(self_ref, req_id, sess_id):
				try:
					resp = await self_ref.browser_session.cdp_client.send.Network.getResponseBody(
						params={'requestId': req_id}, session_id=sess_id
					)
					data = resp.get('body', b'')
					if resp.get('base64Encoded'):
						import base64 as _b64

						data = _b64.b64decode(data)
					else:
						# Ensure data is bytes even if CDP returns a string
						if isinstance(data, str):
							data = data.encode('utf-8', errors='replace')
					# Ensure we always have bytes
					if not isinstance(data, bytes):
						data = bytes(data) if data else b''
					entry.response_body = data
				except Exception:
					pass

			# Always schedule the response body fetch task
			_asyncio.create_task(_fetch_body(self, request_id, session_id))

			encoded_length = (
				params.get('encodedDataLength') if hasattr(params, 'get') else getattr(params, 'encodedDataLength', None)
			)
			if encoded_length is not None:
				try:
					entry.encoded_data_length = int(encoded_length)
					entry.transfer_size = entry.encoded_data_length
				except Exception:
					entry.encoded_data_length = None
		except Exception as e:
			self.logger.debug(f'loadingFinished handling error: {e}')