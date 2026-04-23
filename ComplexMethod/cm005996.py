def test_query_with_quotes(self, mock_client_cls, mock_from_file, component_class, default_kwargs):
        """Test that queries wrapped in quotes are properly handled."""
        # Arrange mocks
        mock_creds = MagicMock(spec=Credentials)
        mock_from_file.return_value = mock_creds

        # Create a mock row that can be converted to a dict
        mock_row = MagicMock()
        mock_row.items.return_value = [("column1", "value1")]
        mock_row.__iter__.return_value = iter([("column1", "value1")])
        mock_row.keys.return_value = ["column1"]
        mock_row.to_numpy.return_value = ["value1"]  # Changed from values to to_numpy
        mock_row.__getitem__.return_value = "value1"

        # Create mock result with the mock row
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter([mock_row])

        # Create mock job with the mock result
        mock_job = MagicMock()
        mock_job.result.return_value = mock_result

        # Create mock client with the mock job
        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_client_cls.return_value = mock_client

        # Test with double quotes
        query_with_double_quotes = '"SELECT * FROM table"'
        component = component_class(**{**default_kwargs, "query": query_with_double_quotes, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with single quotes
        query_with_single_quotes = "'SELECT * FROM table'"
        component = component_class(**{**default_kwargs, "query": query_with_single_quotes, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with SQL code block
        query_with_code_block = "```sql\nSELECT * FROM table\n```"
        component = component_class(**{**default_kwargs, "query": query_with_code_block, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with SQL code block and quotes
        query_with_code_block_and_quotes = '```sql\n"SELECT * FROM table"\n```'
        component = component_class(
            **{**default_kwargs, "query": query_with_code_block_and_quotes, "clean_query": True}
        )
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with just backticks
        query_with_backticks = "`SELECT * FROM table`"
        component = component_class(**{**default_kwargs, "query": query_with_backticks, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with mixed markers
        query_with_mixed = '```sql\n`"SELECT * FROM table"`\n```'
        component = component_class(**{**default_kwargs, "query": query_with_mixed, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with backticks in the middle of the query
        query_with_middle_backticks = "SELECT * FROM project.dataset.table"
        component = component_class(**{**default_kwargs, "query": query_with_middle_backticks, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM project.dataset.table")
        assert isinstance(result, DataFrame)

        # Reset mocks for next test
        mock_client.reset_mock()

        # Test with multiple backticks in the query
        query_with_multiple_backticks = "SELECT * FROM project.dataset.table WHERE column = 'value'"
        component = component_class(**{**default_kwargs, "query": query_with_multiple_backticks, "clean_query": True})
        result = component.execute_sql()
        mock_client.query.assert_called_once_with("SELECT * FROM project.dataset.table WHERE column = 'value'")
        assert isinstance(result, DataFrame)