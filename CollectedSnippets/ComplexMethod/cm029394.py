async def poll_for_token(
		self,
		device_code: str,
		interval: float = 3.0,
		timeout: float = 1800.0,
	) -> dict | None:
		"""
		Poll for the access token.
		Returns token info when authorized, None if timeout.
		"""
		start_time = time.time()

		if self.http_client:
			# Use injected client for all requests
			while time.time() - start_time < timeout:
				try:
					response = await self.http_client.post(
						f'{self.base_url.rstrip("/")}/api/v1/oauth/device/token',
						data={
							'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
							'device_code': device_code,
							'client_id': self.client_id,
						},
					)

					if response.status_code == 200:
						data = response.json()

						# Check for pending authorization
						if data.get('error') == 'authorization_pending':
							await asyncio.sleep(interval)
							continue

						# Check for slow down
						if data.get('error') == 'slow_down':
							interval = data.get('interval', interval * 2)
							await asyncio.sleep(interval)
							continue

						# Check for other errors
						if 'error' in data:
							print(f'Error: {data.get("error_description", data["error"])}')
							return None

						# Success! We have a token
						if 'access_token' in data:
							return data

					elif response.status_code == 400:
						# Error response
						data = response.json()
						if data.get('error') not in ['authorization_pending', 'slow_down']:
							print(f'Error: {data.get("error_description", "Unknown error")}')
							return None

					else:
						print(f'Unexpected status code: {response.status_code}')
						return None

				except Exception as e:
					print(f'Error polling for token: {e}')

				await asyncio.sleep(interval)
		else:
			# Create a new client for polling
			async with httpx.AsyncClient() as client:
				while time.time() - start_time < timeout:
					try:
						response = await client.post(
							f'{self.base_url.rstrip("/")}/api/v1/oauth/device/token',
							data={
								'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
								'device_code': device_code,
								'client_id': self.client_id,
							},
						)

						if response.status_code == 200:
							data = response.json()

							# Check for pending authorization
							if data.get('error') == 'authorization_pending':
								await asyncio.sleep(interval)
								continue

							# Check for slow down
							if data.get('error') == 'slow_down':
								interval = data.get('interval', interval * 2)
								await asyncio.sleep(interval)
								continue

							# Check for other errors
							if 'error' in data:
								print(f'Error: {data.get("error_description", data["error"])}')
								return None

							# Success! We have a token
							if 'access_token' in data:
								return data

						elif response.status_code == 400:
							# Error response
							data = response.json()
							if data.get('error') not in ['authorization_pending', 'slow_down']:
								print(f'Error: {data.get("error_description", "Unknown error")}')
								return None

						else:
							print(f'Unexpected status code: {response.status_code}')
							return None

					except Exception as e:
						print(f'Error polling for token: {e}')

					await asyncio.sleep(interval)

		return None