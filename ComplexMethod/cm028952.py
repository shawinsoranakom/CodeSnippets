async def test_act_enforces_per_action_timeout_on_hung_handler():
	"""tools.act() must return within action_timeout even if the handler hangs."""
	tools = Tools()

	# Replace the action executor with one that hangs far past the timeout.
	sleep_seconds = 30.0
	call_count = {'n': 0}

	async def _hanging_execute_action(**_kwargs):
		call_count['n'] += 1
		await asyncio.sleep(sleep_seconds)
		return ActionResult(extracted_content='should never be reached')

	tools.registry.execute_action = _hanging_execute_action  # type: ignore[assignment]

	# Build an ActionModel with a single slot — act() iterates model_dump(exclude_unset=True).
	action = _StubActionModel(hung_action={'url': 'https://example.com'})

	# Use a tight timeout so the test runs in under a second.
	action_timeout = 0.5
	start = time.monotonic()
	result = await tools.act(action=action, browser_session=None, action_timeout=action_timeout)  # type: ignore[arg-type]
	elapsed = time.monotonic() - start

	# Handler got invoked exactly once.
	assert call_count['n'] == 1

	# Returned well before the sleep would have finished.
	assert elapsed < sleep_seconds / 2, f'act() did not honor timeout; took {elapsed:.2f}s'
	# And returned close to the timeout itself (with a reasonable grace margin).
	assert elapsed < action_timeout + 2.0, f'act() overshot timeout; took {elapsed:.2f}s'

	# Returned a proper ActionResult describing the timeout.
	assert isinstance(result, ActionResult)
	assert result.error is not None
	assert 'timed out' in result.error.lower()
	assert 'hung_action' in result.error