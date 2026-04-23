async def test_process_body(self, component):
        # Test body processing
        # Test dictionary body
        dict_body = {"key": "value", "nested": {"inner": "value"}}
        assert component._process_body(dict_body) == dict_body

        # Test string body
        json_str = '{"key": "value"}'
        assert component._process_body(json_str) == {"key": "value"}

        # Test list body
        list_body = [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}]
        assert component._process_body(list_body) == {"key1": "value1", "key2": "value2"}

        # Test Data object body
        data_body = Data(data={"id": 123, "name": "John Doe"})
        assert component._process_body(data_body) == {"id": 123, "name": "John Doe"}

        # Test nested Data object (Data containing dict)
        nested_data_body = Data(data={"user": {"id": 456, "email": "test@example.com"}})
        assert component._process_body(nested_data_body) == {"user": {"id": 456, "email": "test@example.com"}}

        # Test invalid body
        assert component._process_body(None) == {}
        assert component._process_body([{"invalid": "format"}]) == {}