async def main():
	print('🚀 Gmail 2FA Integration Example with Grant Mechanism')
	print('=' * 60)

	# Initialize grant manager
	grant_manager = GmailGrantManager()

	# Step 1: Check and validate credentials
	print('🔍 Step 1: Validating Gmail credentials...')

	if not grant_manager.check_credentials_exist():
		print('❌ No Gmail credentials found')
		setup_success = await grant_manager.setup_oauth_credentials()
		if not setup_success:
			print('⏹️  Setup cancelled or failed. Exiting...')
			return
	else:
		is_valid, error = grant_manager.validate_credentials_format()
		if not is_valid:
			print(f'❌ Invalid credentials: {error}')
			setup_success = await grant_manager.setup_oauth_credentials()
			if not setup_success:
				print('⏹️  Setup cancelled or failed. Exiting...')
				return
		else:
			print('✅ Gmail credentials file found and validated')

	# Step 2: Initialize Gmail service and test authentication
	print('\n🔍 Step 2: Testing Gmail authentication...')

	gmail_service = GmailService()
	auth_success, auth_message = await grant_manager.test_authentication(gmail_service)

	if not auth_success:
		print(f'❌ Initial authentication failed: {auth_message}')
		recovery_success = await grant_manager.handle_authentication_failure(gmail_service, auth_message)

		if not recovery_success:
			print('❌ Failed to recover Gmail authentication. Please check your setup.')
			return

	# Step 3: Initialize tools with authenticated service
	print('\n🔍 Step 3: Registering Gmail actions...')

	tools = Tools()
	register_gmail_actions(tools, gmail_service=gmail_service)

	print('✅ Gmail actions registered with tools')
	print('Available Gmail actions:')
	print('- get_recent_emails: Get recent emails with filtering')
	print()

	# Initialize LLM
	llm = ChatOpenAI(model='gpt-4.1-mini')

	# Step 4: Test Gmail functionality
	print('🔍 Step 4: Testing Gmail email retrieval...')

	agent = Agent(task='Get recent emails from Gmail to test the integration is working properly', llm=llm, tools=tools)

	try:
		history = await agent.run()
		print('✅ Gmail email retrieval test completed')
	except Exception as e:
		print(f'❌ Gmail email retrieval test failed: {e}')
		# Try one more recovery attempt
		print('🔧 Attempting final recovery...')
		recovery_success = await grant_manager.handle_authentication_failure(gmail_service, str(e))
		if recovery_success:
			print('✅ Recovery successful, re-running test...')
			history = await agent.run()
		else:
			print('❌ Final recovery failed. Please check your Gmail API setup.')
			return

	print('\n' + '=' * 60)

	# Step 5: Demonstrate 2FA code finding
	print('🔍 Step 5: Testing 2FA code detection...')

	agent2 = Agent(
		task='Search for any 2FA verification codes or OTP codes in recent Gmail emails from the last 30 minutes',
		llm=llm,
		tools=tools,
	)

	history2 = await agent2.run()
	print('✅ 2FA code search completed')

	print('\n' + '=' * 60)

	# Step 6: Simulate complete login flow
	print('🔍 Step 6: Demonstrating complete 2FA login flow...')

	agent3 = Agent(
		task="""
		Demonstrate a complete 2FA-enabled login flow:
		1. Check for any existing 2FA codes in recent emails
		2. Explain how the agent would handle a typical login:
		   - Navigate to a login page
		   - Enter credentials
		   - Wait for 2FA prompt
		   - Use get_recent_emails to find the verification code
		   - Extract and enter the 2FA code
		3. Show what types of emails and codes can be detected
		""",
		llm=llm,
		tools=tools,
	)

	history3 = await agent3.run()
	print('✅ Complete 2FA flow demonstration completed')

	print('\n' + '=' * 60)
	print('🎉 Gmail 2FA Integration with Grant Mechanism completed successfully!')
	print('\n💡 Key features demonstrated:')
	print('- ✅ Automatic credential validation and setup')
	print('- ✅ Robust error handling and recovery mechanisms')
	print('- ✅ Interactive OAuth grant flow')
	print('- ✅ Token refresh and re-authentication')
	print('- ✅ 2FA code detection and extraction')
	print('\n🔧 Grant mechanism benefits:')
	print('- Handles missing or invalid credentials gracefully')
	print('- Provides clear setup instructions')
	print('- Automatically recovers from authentication failures')
	print('- Validates credential format before use')
	print('- Offers multiple fallback options')