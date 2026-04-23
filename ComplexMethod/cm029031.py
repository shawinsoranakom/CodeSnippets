async def test_from_state_with_json_csv_files(self, temp_filesystem):
		"""Test restoring filesystem from state with JSON and CSV files."""
		fs = temp_filesystem

		# Add JSON and CSV content
		await fs.write_file('data.json', '{"version": "1.0", "users": [{"name": "John", "age": 30}]}')
		await fs.write_file('users.csv', 'name,age,city\nJohn,30,New York\nJane,25,London')
		await fs.write_file('config.json', '{"debug": true, "port": 8080}')
		await fs.write_file('products.csv', 'id,name,price\n1,Laptop,999.99\n2,Mouse,29.99')

		# Get state
		state = fs.get_state()

		# Create new filesystem from state
		fs2 = FileSystem.from_state(state)

		# Verify restoration
		assert fs2.base_dir == fs.base_dir
		assert len(fs2.files) == len(fs.files)

		# Verify JSON file contents
		json_file = fs2.get_file('data.json')
		assert json_file is not None
		assert isinstance(json_file, JsonFile)
		assert json_file.content == '{"version": "1.0", "users": [{"name": "John", "age": 30}]}'

		config_file = fs2.get_file('config.json')
		assert config_file is not None
		assert isinstance(config_file, JsonFile)
		assert config_file.content == '{"debug": true, "port": 8080}'

		# Verify CSV file contents
		csv_file = fs2.get_file('users.csv')
		assert csv_file is not None
		assert isinstance(csv_file, CsvFile)
		assert csv_file.content == 'name,age,city\nJohn,30,New York\nJane,25,London'

		products_file = fs2.get_file('products.csv')
		assert products_file is not None
		assert isinstance(products_file, CsvFile)
		assert products_file.content == 'id,name,price\n1,Laptop,999.99\n2,Mouse,29.99'

		# Verify files exist on disk
		assert (fs2.data_dir / 'data.json').exists()
		assert (fs2.data_dir / 'users.csv').exists()
		assert (fs2.data_dir / 'config.json').exists()
		assert (fs2.data_dir / 'products.csv').exists()

		# Verify disk contents match
		assert (fs2.data_dir / 'data.json').read_text() == '{"version": "1.0", "users": [{"name": "John", "age": 30}]}'
		assert (fs2.data_dir / 'users.csv').read_text() == 'name,age,city\nJohn,30,New York\nJane,25,London'

		# Clean up second filesystem
		fs2.nuke()