def test_read_from_dict(self):
        """Test creating ParameterSweep from a dict format."""
        data = {
            "experiment1": {"max_tokens": 100, "temperature": 0.7},
            "experiment2": {"max_tokens": 200, "temperature": 0.9},
        }
        sweep = ParameterSweep.read_from_dict(data)
        assert len(sweep) == 2

        # Check that items have the _benchmark_name field
        names = {item["_benchmark_name"] for item in sweep}
        assert names == {"experiment1", "experiment2"}

        # Check that parameters are preserved
        for item in sweep:
            if item["_benchmark_name"] == "experiment1":
                assert item["max_tokens"] == 100
                assert item["temperature"] == 0.7
            elif item["_benchmark_name"] == "experiment2":
                assert item["max_tokens"] == 200
                assert item["temperature"] == 0.9