async def _load_storage_state(self, path: str | None = None) -> None:
		"""Load browser storage state from file."""
		if not self.browser_session.cdp_client:
			self.logger.warning('[StorageStateWatchdog] No CDP client available for loading')
			return

		load_path = path or self.browser_session.browser_profile.storage_state
		if not load_path or not os.path.exists(str(load_path)):
			return

		try:
			# Read the storage state file asynchronously
			import anyio

			content = await anyio.Path(str(load_path)).read_text()
			storage = json.loads(content)

			# Apply cookies if present
			if 'cookies' in storage and storage['cookies']:
				# Playwright exports session cookies with expires=0/-1. CDP treats expires=0 as expired.
				# Normalize session cookies by omitting expires
				normalized_cookies: list[Cookie] = []
				for cookie in storage['cookies']:
					if not isinstance(cookie, dict):
						normalized_cookies.append(cookie)  # type: ignore[arg-type]
						continue
					c = dict(cookie)
					expires = c.get('expires')
					if expires in (0, 0.0, -1, -1.0):
						c.pop('expires', None)
					normalized_cookies.append(Cookie(**c))

				await self.browser_session._cdp_set_cookies(normalized_cookies)
				self._last_cookie_state = storage['cookies'].copy()
				self.logger.debug(f'[StorageStateWatchdog] Added {len(storage["cookies"])} cookies from storage state')

			# Apply origins (localStorage/sessionStorage) if present
			if 'origins' in storage and storage['origins']:
				for origin in storage['origins']:
					origin_value = origin.get('origin')
					if not origin_value:
						continue

					# Scope storage restoration to its origin to avoid cross-site pollution.
					if origin.get('localStorage'):
						lines = []
						for item in origin['localStorage']:
							lines.append(f'window.localStorage.setItem({json.dumps(item["name"])}, {json.dumps(item["value"])});')
						script = (
							'(function(){\n'
							f'  if (window.location && window.location.origin !== {json.dumps(origin_value)}) return;\n'
							'  try {\n'
							f'    {" ".join(lines)}\n'
							'  } catch (e) {}\n'
							'})();'
						)
						await self.browser_session._cdp_add_init_script(script)

					if origin.get('sessionStorage'):
						lines = []
						for item in origin['sessionStorage']:
							lines.append(
								f'window.sessionStorage.setItem({json.dumps(item["name"])}, {json.dumps(item["value"])});'
							)
						script = (
							'(function(){\n'
							f'  if (window.location && window.location.origin !== {json.dumps(origin_value)}) return;\n'
							'  try {\n'
							f'    {" ".join(lines)}\n'
							'  } catch (e) {}\n'
							'})();'
						)
						await self.browser_session._cdp_add_init_script(script)
				self.logger.debug(
					f'[StorageStateWatchdog] Applied localStorage/sessionStorage from {len(storage["origins"])} origins'
				)

			self.event_bus.dispatch(
				StorageStateLoadedEvent(
					path=str(load_path),
					cookies_count=len(storage.get('cookies', [])),
					origins_count=len(storage.get('origins', [])),
				)
			)

			self.logger.debug(f'[StorageStateWatchdog] Loaded storage state from: {load_path}')

		except Exception as e:
			self.logger.error(f'[StorageStateWatchdog] Failed to load storage state: {e}')