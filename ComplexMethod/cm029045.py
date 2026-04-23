async def capture_dom_state(label: str) -> dict:
			"""Capture DOM state and return analysis"""
			print(f'\n📸 Capturing DOM state: {label}')
			state_event = browser_session.event_bus.dispatch(
				BrowserStateRequestEvent(include_dom=True, include_screenshot=False, include_recent_events=False)
			)
			browser_state = await state_event.event_result()

			if browser_state and browser_state.dom_state and browser_state.dom_state.selector_map:
				selector_map = browser_state.dom_state.selector_map
				element_count = len(selector_map)

				# Check for specific elements
				found_elements = {}
				expected_checks = [
					('First Name', ['firstName', 'first name']),
					('Last Name', ['lastName', 'last name']),
					('Email', ['email']),
					('City', ['city']),
					('State', ['state']),
					('Zip', ['zip', 'zipCode']),
				]

				for name, keywords in expected_checks:
					for index, element in selector_map.items():
						element_str = str(element).lower()
						if any(kw.lower() in element_str for kw in keywords):
							found_elements[name] = True
							break

				return {
					'label': label,
					'total_elements': element_count,
					'found_elements': found_elements,
					'selector_map': selector_map,
				}
			return {'label': label, 'error': 'No DOM state available'}