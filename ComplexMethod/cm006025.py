def test_directory_as_dataframe(self):
        """Test DirectoryComponent's as_dataframe method."""
        directory_component = DirectoryComponent()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with different content
            files_content = {
                "file1.txt": "content1",
                "file2.json": '{"key": "content2"}',
                "file3.md": "# content3",
            }

            for filename, content in files_content.items():
                (Path(temp_dir) / filename).write_text(content, encoding="utf-8")

            directory_component.set_attributes(
                {
                    "path": str(temp_dir),
                    "use_multithreading": False,
                    "types": ["txt", "json", "md"],
                    "silent_errors": False,
                }
            )

            # Test as_dataframe
            data_frame = directory_component.as_dataframe()

            # Verify DataFrame structure
            assert isinstance(data_frame, DataFrame), "Expected DataFrame instance"
            assert len(data_frame) == 3, f"Expected DataFrame with 3 rows, got {len(data_frame)}"

            # Check column names
            expected_columns = ["text", "file_path"]
            actual_columns = list(data_frame.columns)
            assert set(expected_columns).issubset(set(actual_columns)), (
                f"Missing required columns. Expected at least {expected_columns}, got {actual_columns}"
            )

            # Verify content matches input files
            texts = data_frame["text"].tolist()
            # For JSON files, the content is parsed and re-serialized
            expected_content = {
                "file1.txt": "content1",
                "file2.json": '{"key":"content2"}',  # JSON is re-serialized without spaces
                "file3.md": "# content3",
            }
            missing_content = [content for content in expected_content.values() if content not in texts]
            assert not missing_content, f"Missing expected content in DataFrame: {missing_content}"

            # Verify file paths are correct
            file_paths = data_frame["file_path"].tolist()
            expected_paths = [str(Path(temp_dir) / filename) for filename in files_content]
            missing_paths = [path for path in expected_paths if not any(path in fp for fp in file_paths)]
            assert not missing_paths, f"Missing expected file paths in DataFrame: {missing_paths}"