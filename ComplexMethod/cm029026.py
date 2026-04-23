async def test_write_csv_file(self, temp_filesystem):
		"""Test writing CSV files."""
		fs = temp_filesystem

		# Write valid CSV content
		csv_content = 'name,age,city\nJohn,30,New York\nJane,25,London\nBob,35,Paris'
		result = await fs.write_file('users.csv', csv_content)
		assert result == 'Data written to file users.csv successfully.'

		# Verify content was written
		content = await fs.read_file('users.csv')
		assert csv_content in content

		# Verify file object was created
		assert 'users.csv' in fs.files
		file_obj = fs.get_file('users.csv')
		assert file_obj is not None
		assert isinstance(file_obj, CsvFile)
		assert file_obj.content == csv_content

		# Write to new CSV file
		result = await fs.write_file('products.csv', 'id,name,price\n1,Laptop,999.99\n2,Mouse,29.99')
		assert result == 'Data written to file products.csv successfully.'
		assert 'products.csv' in fs.files