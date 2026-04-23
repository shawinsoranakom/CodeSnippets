def test_build_custom_groups(self):
        """Test building custom argument groups from reference."""
        reference = {
            "/equity/price/historical": {
                "parameters": {
                    "standard": [],
                    "fmp": [
                        {
                            "name": "interval",
                            "type": "Literal['1min', '5min', '15min']",
                            "description": "Time interval",
                            "default": "1min",
                            "optional": True,
                            "standard": False,
                            "choices": None,
                        }
                    ],
                }
            }
        }

        processor = ReferenceToArgumentsProcessor(reference)
        groups = processor.custom_groups

        assert "/equity/price/historical" in groups
        assert len(groups["/equity/price/historical"]) == 1
        assert groups["/equity/price/historical"][0].name == "fmp"
        assert len(groups["/equity/price/historical"][0].arguments) == 1

        arg = groups["/equity/price/historical"][0].arguments[0]
        assert arg.name == "interval"
        assert arg.type is str
        assert arg.default == "1min"
        assert not arg.required
        assert set(arg.choices) == {"1min", "5min", "15min"}