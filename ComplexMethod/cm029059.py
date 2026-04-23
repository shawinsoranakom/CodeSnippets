async def main():
	if not GOOGLE_API_KEY:
		print('❌ Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable')
		return

	print('WhatsApp Scheduler')
	print(f'Profile: {USER_DATA_DIR}')
	print()

	# Auto mode - respond to unread messages periodically
	if args.auto:
		print('AUTO MODE - Responding to unread messages every ~30 minutes')
		print('Press Ctrl+C to stop.\n')

		while True:
			try:
				await auto_respond_to_unread()

				# Wait 30 minutes +/- 5 minutes randomly
				wait_minutes = 30 + random.randint(-5, 5)
				print(f'\n⏰ Next check in {wait_minutes} minutes...')
				await asyncio.sleep(wait_minutes * 60)

			except KeyboardInterrupt:
				print('\n\nAuto mode stopped by user')
				break
			except Exception as e:
				print(f'\n❌ Error in auto mode: {e}')
				print('Waiting 5 minutes before retry...')
				await asyncio.sleep(300)
		return

	# Parse messages
	print('Parsing messages.txt...')
	messages = await parse_messages()

	if not messages:
		print('No messages found')
		return

	print(f'\nFound {len(messages)} messages:')
	for msg in messages:
		print(f'  • {msg["datetime"]}: {msg["message"][:30]}... to {msg["contact"]}')

	now = datetime.now()
	immediate = []
	future = []

	for msg in messages:
		msg_time = datetime.strptime(msg['datetime'], '%Y-%m-%d %H:%M')
		if msg_time <= now:
			immediate.append(msg)
		else:
			future.append(msg)

	if args.test:
		print('\n=== TEST MODE - Preview ===')
		if immediate:
			print(f'\nWould send {len(immediate)} past-due messages NOW:')
			for msg in immediate:
				print(f'  📱 To {msg["contact"]}: {msg["message"]}')
		if future:
			print(f'\nWould monitor {len(future)} future messages:')
			for msg in future:
				print(f'  ⏰ {msg["datetime"]}: To {msg["contact"]}: {msg["message"]}')
		print('\nTest mode complete. No messages sent.')
		return

	if immediate:
		print(f'\nSending {len(immediate)} past-due messages NOW...')
		for msg in immediate:
			await send_message(msg['contact'], msg['message'])

	if future:
		print(f'\n⏰ Monitoring {len(future)} future messages...')
		print('Press Ctrl+C to stop.\n')

		last_status = None

		while future:
			now = datetime.now()
			due = []
			remaining = []

			for msg in future:
				msg_time = datetime.strptime(msg['datetime'], '%Y-%m-%d %H:%M')
				if msg_time <= now:
					due.append(msg)
				else:
					remaining.append(msg)

			for msg in due:
				print(f'\n⏰ Time reached for {msg["contact"]}')
				await send_message(msg['contact'], msg['message'])

			future = remaining

			if future:
				next_msg = min(future, key=lambda x: datetime.strptime(x['datetime'], '%Y-%m-%d %H:%M'))
				current_status = f'Next: {next_msg["datetime"]} to {next_msg["contact"]}'

				if current_status != last_status:
					print(current_status)
					last_status = current_status

				await asyncio.sleep(30)  # Check every 30 seconds

	print('\n✅ All messages processed!')