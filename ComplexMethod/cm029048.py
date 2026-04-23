def main():
	"""Run a basic cloud automation task."""
	print('🚀 Browser Use Cloud - Basic Task Example')
	print('=' * 50)

	# Define a simple search task (using DuckDuckGo to avoid captchas)
	task_description = (
		"Go to DuckDuckGo and search for 'browser automation tools'. Tell me the top 3 results with their titles and URLs."
	)

	try:
		# Step 1: Create the task
		task_id = create_task(task_description)

		# Step 2: Wait for completion
		result = wait_for_completion(task_id)

		# Step 3: Display results
		print('\n📊 Results:')
		print('-' * 30)
		print(f'Status: {result["status"]}')
		print(f'Steps taken: {len(result.get("steps", []))}')

		if result.get('output'):
			print(f'Output: {result["output"]}')
		else:
			print('No output available')

		# Show share URLs for viewing execution
		if result.get('live_url'):
			print(f'\n🔗 Live Preview: {result["live_url"]}')
		if result.get('public_share_url'):
			print(f'🌐 Share URL: {result["public_share_url"]}')
		elif result.get('share_url'):
			print(f'🌐 Share URL: {result["share_url"]}')

		if not result.get('live_url') and not result.get('public_share_url') and not result.get('share_url'):
			print("\n💡 Tip: Add 'enable_public_share': True to task payload to get shareable URLs")

	except requests.exceptions.RequestException as e:
		print(f'❌ API Error: {e}')
	except Exception as e:
		print(f'❌ Error: {e}')