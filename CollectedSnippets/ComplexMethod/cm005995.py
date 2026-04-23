def test_complex_query_result(self, mock_client_cls, mock_from_file, component_class, default_kwargs):
        """Complex row structures should be correctly serialized to DataFrame."""
        # Arrange mocks
        mock_creds = MagicMock(spec=Credentials)
        mock_from_file.return_value = mock_creds

        # Create mock rows with complex data
        mock_row1 = MagicMock()
        mock_row1.items.return_value = [("id", 1), ("name", "Test 1"), ("value", 10.5), ("active", True)]
        mock_row1.__iter__.return_value = iter([("id", 1), ("name", "Test 1"), ("value", 10.5), ("active", True)])
        mock_row1.keys.return_value = ["id", "name", "value", "active"]
        mock_row1.to_numpy.return_value = [1, "Test 1", 10.5, True]  # Changed from values to to_numpy
        mock_row1.__getitem__.side_effect = lambda key: {"id": 1, "name": "Test 1", "value": 10.5, "active": True}[key]

        mock_row2 = MagicMock()
        mock_row2.items.return_value = [("id", 2), ("name", "Test 2"), ("value", 20.75), ("active", False)]
        mock_row2.__iter__.return_value = iter([("id", 2), ("name", "Test 2"), ("value", 20.75), ("active", False)])
        mock_row2.keys.return_value = ["id", "name", "value", "active"]
        mock_row2.to_numpy.return_value = [2, "Test 2", 20.75, False]  # Changed from values to to_numpy
        mock_row2.__getitem__.side_effect = lambda key: {"id": 2, "name": "Test 2", "value": 20.75, "active": False}[
            key
        ]

        # Create mock result with the mock rows
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter([mock_row1, mock_row2])

        # Create mock job with the mock result
        mock_job = MagicMock()
        mock_job.result.return_value = mock_result

        # Create mock client with the mock job
        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_client_cls.return_value = mock_client

        # Instantiate component with defaults
        component = component_class(**default_kwargs)

        # Execute
        result = component.execute_sql()

        # Verify the result
        assert isinstance(result, DataFrame)
        assert len(result) == 2  # Check number of rows
        assert list(result.columns) == ["id", "name", "value", "active"]  # Check columns

        # Convert DataFrame to dictionary for easier comparison
        result_dict = result.to_dict(orient="records")

        # Verify first row
        assert result_dict[0]["id"] == 1
        assert result_dict[0]["name"] == "Test 1"
        assert result_dict[0]["value"] == 10.5
        assert result_dict[0]["active"] is True

        # Verify second row
        assert result_dict[1]["id"] == 2
        assert result_dict[1]["name"] == "Test 2"
        assert result_dict[1]["value"] == 20.75
        assert result_dict[1]["active"] is False

        # Verify the mocks were called correctly
        mock_from_file.assert_called_once_with(default_kwargs["service_account_json_file"])
        mock_client_cls.assert_called_once_with(credentials=mock_creds, project="test-project")
        mock_client.query.assert_called_once_with(default_kwargs["query"])