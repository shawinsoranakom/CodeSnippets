async def setup_oauth_credentials(self) -> bool:
		"""
		Guide user through OAuth credentials setup process.
		Returns True if setup is successful.
		"""
		print('\n🔐 Gmail OAuth Credentials Setup Required')
		print('=' * 50)

		if not self.check_credentials_exist():
			print('❌ Gmail credentials file not found')
		else:
			is_valid, error = self.validate_credentials_format()
			if not is_valid:
				print(f'❌ Gmail credentials file is invalid: {error}')

		print('\n📋 To set up Gmail API access:')
		print('1. Go to https://console.cloud.google.com/')
		print('2. Create a new project or select an existing one')
		print('3. Enable the Gmail API:')
		print('   - Go to "APIs & Services" > "Library"')
		print('   - Search for "Gmail API" and enable it')
		print('4. Create OAuth 2.0 credentials:')
		print('   - Go to "APIs & Services" > "Credentials"')
		print('   - Click "Create Credentials" > "OAuth client ID"')
		print('   - Choose "Desktop application"')
		print('   - Download the JSON file')
		print(f'5. Save the JSON file as: {self.credentials_file}')
		print(f'6. Ensure the directory exists: {self.config_dir}')

		# Create config directory if it doesn't exist
		self.config_dir.mkdir(parents=True, exist_ok=True)
		print(f'\n✅ Created config directory: {self.config_dir}')

		# Wait for user to set up credentials
		while True:
			user_input = input('\n❓ Have you saved the credentials file? (y/n/skip): ').lower().strip()

			if user_input == 'skip':
				print('⏭️  Skipping credential validation for now')
				return False
			elif user_input == 'y':
				if self.check_credentials_exist():
					is_valid, error = self.validate_credentials_format()
					if is_valid:
						print('✅ Credentials file found and validated!')
						return True
					else:
						print(f'❌ Credentials file is invalid: {error}')
						print('Please check the file format and try again.')
				else:
					print(f'❌ Credentials file still not found at: {self.credentials_file}')
			elif user_input == 'n':
				print('⏳ Please complete the setup steps above and try again.')
			else:
				print('Please enter y, n, or skip')