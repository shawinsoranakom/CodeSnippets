async def handle_connection(
		self,
		reader: asyncio.StreamReader,
		writer: asyncio.StreamWriter,
	) -> None:
		"""Handle a single client request (one command per connection)."""
		try:
			line = await asyncio.wait_for(reader.readline(), timeout=300)
			if not line:
				return

			request = {}
			try:
				import hmac

				request = json.loads(line.decode())
				req_id = request.get('id', '')
				# Reject requests that don't carry the correct auth token.
				# Use hmac.compare_digest to prevent timing-oracle attacks.
				if self._auth_token and not hmac.compare_digest(
					request.get('token', ''),
					self._auth_token,
				):
					response = {'id': req_id, 'success': False, 'error': 'Unauthorized'}
				else:
					response = await self.dispatch(request)
			except json.JSONDecodeError as e:
				response = {'id': '', 'success': False, 'error': f'Invalid JSON: {e}'}
			except Exception as e:
				logger.exception(f'Error handling request: {e}')
				response = {'id': '', 'success': False, 'error': str(e)}

			writer.write((json.dumps(response) + '\n').encode())
			await writer.drain()

			if response.get('success') and request.get('action') == 'shutdown':
				self._request_shutdown()

		except TimeoutError:
			logger.debug('Connection timeout')
		except Exception as e:
			logger.exception(f'Connection error: {e}')
		finally:
			writer.close()
			try:
				await writer.wait_closed()
			except Exception:
				pass