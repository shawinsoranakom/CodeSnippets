async def run_auth_command():
	"""Run the authentication command with dummy task in UI."""
	import asyncio
	import os

	from browser_use.sync.auth import DeviceAuthClient

	print('🔐 Browser Use Cloud Authentication')
	print('=' * 40)

	# Ensure cloud sync is enabled (should be default, but make sure)
	os.environ['BROWSER_USE_CLOUD_SYNC'] = 'true'

	auth_client = DeviceAuthClient()

	print('🔍 Debug: Checking authentication status...')
	print(f'    API Token: {"✅ Present" if auth_client.api_token else "❌ Missing"}')
	print(f'    User ID: {auth_client.user_id}')
	print(f'    Is Authenticated: {auth_client.is_authenticated}')
	if auth_client.auth_config.authorized_at:
		print(f'    Authorized at: {auth_client.auth_config.authorized_at}')
	print()

	# Check if already authenticated
	if auth_client.is_authenticated:
		print('✅ Already authenticated!')
		print(f'   User ID: {auth_client.user_id}')
		print(f'   Authenticated at: {auth_client.auth_config.authorized_at}')

		# Show cloud URL if possible
		frontend_url = CONFIG.BROWSER_USE_CLOUD_UI_URL or auth_client.base_url.replace('//api.', '//cloud.')
		print(f'\n🌐 View your runs at: {frontend_url}')
		return

	print('🚀 Starting authentication flow...')
	print('   This will open a browser window for you to sign in.')
	print()

	# Initialize variables for exception handling
	task_id = None
	sync_service = None

	try:
		# Create authentication flow with dummy task
		from uuid_extensions import uuid7str

		from browser_use.agent.cloud_events import (
			CreateAgentSessionEvent,
			CreateAgentStepEvent,
			CreateAgentTaskEvent,
			UpdateAgentTaskEvent,
		)
		from browser_use.sync.service import CloudSync

		# IDs for our session and task
		session_id = uuid7str()
		task_id = uuid7str()

		# Create special sync service that allows auth events
		sync_service = CloudSync(allow_session_events_for_auth=True)
		sync_service.set_auth_flow_active()  # Explicitly enable auth flow
		sync_service.session_id = session_id  # Set session ID for auth context
		sync_service.auth_client = auth_client  # Use the same auth client instance!

		# 1. Create session (like main branch does at start)
		session_event = CreateAgentSessionEvent(
			id=session_id,
			user_id=auth_client.temp_user_id,
			browser_session_id=uuid7str(),
			browser_session_live_url='',
			browser_session_cdp_url='',
			device_id=auth_client.device_id,
			browser_state={
				'viewport': {'width': 1280, 'height': 720},
				'user_agent': None,
				'headless': True,
				'initial_url': None,
				'final_url': None,
				'total_pages_visited': 0,
				'session_duration_seconds': 0,
			},
			browser_session_data={
				'cookies': [],
				'secrets': {},
				'allowed_domains': [],
			},
		)
		await sync_service.handle_event(session_event)

		# Brief delay to ensure session is created in backend before sending task
		await asyncio.sleep(0.5)

		# 2. Create task (like main branch does at start)
		task_event = CreateAgentTaskEvent(
			id=task_id,
			agent_session_id=session_id,
			llm_model='auth-flow',
			task='🔐 Complete authentication and join the browser-use community',
			user_id=auth_client.temp_user_id,
			device_id=auth_client.device_id,
			done_output=None,
			user_feedback_type=None,
			user_comment=None,
			gif_url=None,
		)
		await sync_service.handle_event(task_event)

		# Longer delay to ensure task is created in backend before sending step event
		await asyncio.sleep(1.0)

		# 3. Run authentication with timeout
		print('⏳ Waiting for authentication... (this may take up to 2 minutes for testing)')
		print('   Complete the authentication in your browser, then this will continue automatically.')
		print()

		try:
			print('🔧 Debug: Starting authentication process...')
			print(f'    Original auth client authenticated: {auth_client.is_authenticated}')
			print(f'    Sync service auth client authenticated: {sync_service.auth_client.is_authenticated}')
			print(f'    Same auth client? {auth_client is sync_service.auth_client}')
			print(f'    Session ID: {sync_service.session_id}')

			# Create a task to show periodic status updates
			async def show_auth_progress():
				for i in range(1, 25):  # Show updates every 5 seconds for 2 minutes
					await asyncio.sleep(5)
					fresh_check = DeviceAuthClient()
					print(f'⏱️  Waiting for authentication... ({i * 5}s elapsed)')
					print(f'    Status: {"✅ Authenticated" if fresh_check.is_authenticated else "⏳ Still waiting"}')
					if fresh_check.is_authenticated:
						print('🎉 Authentication detected! Completing...')
						break

			# Run authentication and progress updates concurrently
			auth_start_time = asyncio.get_event_loop().time()
			from browser_use.utils import create_task_with_error_handling

			auth_task = create_task_with_error_handling(
				sync_service.authenticate(show_instructions=True), name='sync_authenticate'
			)
			progress_task = create_task_with_error_handling(
				show_auth_progress(), name='show_auth_progress', suppress_exceptions=True
			)

			# Wait for authentication to complete, with timeout
			success = await asyncio.wait_for(auth_task, timeout=120.0)  # 2 minutes for initial testing
			progress_task.cancel()  # Stop the progress updates

			auth_duration = asyncio.get_event_loop().time() - auth_start_time
			print(f'🔧 Debug: Authentication returned: {success} (took {auth_duration:.1f}s)')

		except TimeoutError:
			print('⏱️ Authentication timed out after 2 minutes.')
			print('   Checking if authentication completed in background...')

			# Create a fresh auth client to check current status
			fresh_auth_client = DeviceAuthClient()
			print('🔧 Debug: Fresh auth client check:')
			print(f'    API Token: {"✅ Present" if fresh_auth_client.api_token else "❌ Missing"}')
			print(f'    Is Authenticated: {fresh_auth_client.is_authenticated}')

			if fresh_auth_client.is_authenticated:
				print('✅ Authentication was successful!')
				success = True
				# Update the sync service's auth client
				sync_service.auth_client = fresh_auth_client
			else:
				print('❌ Authentication not completed. Please try again.')
				success = False
		except Exception as e:
			print(f'❌ Authentication error: {type(e).__name__}: {e}')
			import traceback

			print(f'📄 Full traceback: {traceback.format_exc()}')
			success = False

		if success:
			# 4. Send step event to show progress (like main branch during execution)
			# Use the sync service's auth client which has the updated user_id
			step_event = CreateAgentStepEvent(
				# Remove explicit ID - let it auto-generate to avoid backend validation issues
				user_id=auth_client.temp_user_id,  # Use same temp user_id as task for consistency
				device_id=auth_client.device_id,  # Use consistent device_id
				agent_task_id=task_id,
				step=1,
				actions=[
					{
						'click': {
							'coordinate': [800, 400],
							'description': 'Click on Star button',
							'success': True,
						},
						'done': {
							'success': True,
							'text': '⭐ Starred browser-use/browser-use repository! Welcome to the community!',
						},
					}
				],
				next_goal='⭐ Star browser-use GitHub repository to join the community',
				evaluation_previous_goal='Authentication completed successfully',
				memory='User authenticated with Browser Use Cloud and is now part of the community',
				screenshot_url=None,
				url='https://github.com/browser-use/browser-use',
			)
			print('📤 Sending dummy step event...')
			await sync_service.handle_event(step_event)

			# Small delay to ensure step is processed before completion
			await asyncio.sleep(0.5)

			# 5. Complete task (like main branch does at end)
			completion_event = UpdateAgentTaskEvent(
				id=task_id,
				user_id=auth_client.temp_user_id,  # Use same temp user_id as task for consistency
				device_id=auth_client.device_id,  # Use consistent device_id
				done_output="🎉 Welcome to Browser Use! You're now authenticated and part of our community. ⭐ Your future tasks will sync to the cloud automatically.",
				user_feedback_type=None,
				user_comment=None,
				gif_url=None,
			)
			await sync_service.handle_event(completion_event)

			print('🎉 Authentication successful!')
			print('   Future browser-use runs will now sync to the cloud.')
		else:
			# Failed - still complete the task with failure message
			completion_event = UpdateAgentTaskEvent(
				id=task_id,
				user_id=auth_client.temp_user_id,  # Still temp user since auth failed
				device_id=auth_client.device_id,
				done_output='❌ Authentication failed. Please try again.',
				user_feedback_type=None,
				user_comment=None,
				gif_url=None,
			)
			await sync_service.handle_event(completion_event)

			print('❌ Authentication failed.')
			print('   Please try again or check your internet connection.')

	except Exception as e:
		print(f'❌ Authentication error: {e}')
		# Still try to complete the task in UI with error message
		if task_id and sync_service:
			try:
				from browser_use.agent.cloud_events import UpdateAgentTaskEvent

				completion_event = UpdateAgentTaskEvent(
					id=task_id,
					user_id=auth_client.temp_user_id,
					device_id=auth_client.device_id,
					done_output=f'❌ Authentication error: {e}',
					user_feedback_type=None,
					user_comment=None,
					gif_url=None,
				)
				await sync_service.handle_event(completion_event)
			except Exception:
				pass  # Don't fail if we can't send the error event
		sys.exit(1)