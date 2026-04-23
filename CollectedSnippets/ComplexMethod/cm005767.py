async def test_concurrent_loading(self, base_components_path):
        """Test concurrent execution of both loading methods."""
        tasks = [
            import_langflow_components(),
            aget_all_types_dict(base_components_path),
            import_langflow_components(),
        ]

        results = await asyncio.gather(*tasks)

        langflow_result1, all_types_result, langflow_result2 = results

        assert isinstance(langflow_result1, dict)
        assert isinstance(langflow_result2, dict)
        assert isinstance(all_types_result, dict)

        assert "components" in langflow_result1
        assert "components" in langflow_result2

        categories1 = set(langflow_result1["components"].keys())
        categories2 = set(langflow_result2["components"].keys())

        for category in categories1.intersection(categories2):
            comps1 = set(langflow_result1["components"][category].keys())
            comps2 = set(langflow_result2["components"][category].keys())
            if comps1 != comps2:
                missing_in_2 = comps1 - comps2
                missing_in_1 = comps2 - comps1
                print(
                    f"Component differences in {category}: "
                    f"missing in result2: {missing_in_2}, missing in result1: {missing_in_1}"
                )