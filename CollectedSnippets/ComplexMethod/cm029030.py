async def test_complete_workflow_with_json_csv(self):
		"""Test a complete filesystem workflow with JSON and CSV files."""
		with tempfile.TemporaryDirectory() as tmp_dir:
			# Create filesystem
			fs = FileSystem(base_dir=tmp_dir, create_default_files=True)

			# Write JSON configuration file
			config_json = '{"app": {"name": "TestApp", "version": "1.0"}, "database": {"host": "localhost", "port": 5432}}'
			await fs.write_file('config.json', config_json)

			# Write CSV data file
			users_csv = 'id,name,email,age\n1,John Doe,john@example.com,30\n2,Jane Smith,jane@example.com,25'
			await fs.write_file('users.csv', users_csv)

			# Append more data to CSV
			await fs.append_file('users.csv', '\n3,Bob Johnson,bob@example.com,35')

			# Update JSON configuration
			updated_config = '{"app": {"name": "TestApp", "version": "1.1"}, "database": {"host": "localhost", "port": 5432}, "features": {"logging": true}}'
			await fs.write_file('config.json', updated_config)

			# Create another JSON file for API responses
			api_response = '{"status": "success", "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]}'
			await fs.write_file('api_response.json', api_response)

			# Create a products CSV file
			products_csv = (
				'sku,name,price,category\nLAP001,Gaming Laptop,1299.99,Electronics\nMOU001,Wireless Mouse,29.99,Accessories'
			)
			await fs.write_file('products.csv', products_csv)

			# Verify file listing
			files = fs.list_files()
			expected_files = ['todo.md', 'config.json', 'users.csv', 'api_response.json', 'products.csv']
			assert len(files) == len(expected_files)
			for expected_file in expected_files:
				assert expected_file in files

			# Verify JSON file contents
			config_file = fs.get_file('config.json')
			assert config_file is not None
			assert isinstance(config_file, JsonFile)
			assert config_file.content == updated_config

			api_file = fs.get_file('api_response.json')
			assert api_file is not None
			assert isinstance(api_file, JsonFile)
			assert api_file.content == api_response

			# Verify CSV file contents
			users_file = fs.get_file('users.csv')
			assert users_file is not None
			assert isinstance(users_file, CsvFile)
			expected_users_content = 'id,name,email,age\n1,John Doe,john@example.com,30\n2,Jane Smith,jane@example.com,25\n3,Bob Johnson,bob@example.com,35'
			assert users_file.content == expected_users_content

			products_file = fs.get_file('products.csv')
			assert products_file is not None
			assert isinstance(products_file, CsvFile)
			assert products_file.content == products_csv

			# Test state persistence with JSON and CSV files
			state = fs.get_state()
			fs.nuke()

			# Restore from state
			fs2 = FileSystem.from_state(state)

			# Verify restoration
			assert len(fs2.files) == len(expected_files)

			# Verify JSON files were restored correctly
			restored_config = fs2.get_file('config.json')
			assert restored_config is not None
			assert isinstance(restored_config, JsonFile)
			assert restored_config.content == updated_config

			restored_api = fs2.get_file('api_response.json')
			assert restored_api is not None
			assert isinstance(restored_api, JsonFile)
			assert restored_api.content == api_response

			# Verify CSV files were restored correctly
			restored_users = fs2.get_file('users.csv')
			assert restored_users is not None
			assert isinstance(restored_users, CsvFile)
			assert restored_users.content == expected_users_content

			restored_products = fs2.get_file('products.csv')
			assert restored_products is not None
			assert isinstance(restored_products, CsvFile)
			assert restored_products.content == products_csv

			# Verify files exist on disk
			for filename in expected_files:
				if filename != 'todo.md':  # Skip todo.md as it's already tested
					assert (fs2.data_dir / filename).exists()

			fs2.nuke()