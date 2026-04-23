def test_update_auto_metadata_via_dataset_update(self, client, add_dataset_func):
        dataset = add_dataset_func

        # Initially set auto-metadata via dataset.update
        payload = {
            "auto_metadata_config": {
                "enabled": True,
                "fields": [
                    {
                        "name": "tags",
                        "type": "list",
                        "description": "Document tags",
                        "examples": ["AI", "ML", "RAG"],
                        "restrict_values": False,
                    }
                ],
            }
        }
        dataset.update(payload)

        cfg = dataset.get_auto_metadata()
        assert cfg["enabled"] is True
        assert len(cfg["fields"]) == 1
        assert cfg["fields"][0]["name"] == "tags"
        assert cfg["fields"][0]["type"] == "list"

        # Disable auto-metadata and replace fields
        update_cfg = {
            "enabled": False,
            "fields": [
                {
                    "name": "year",
                    "type": "time",
                    "description": "Publication year",
                    "examples": None,
                    "restrict_values": False,
                }
            ],
        }
        dataset.update_auto_metadata(**update_cfg)

        cfg2 = dataset.get_auto_metadata()
        assert cfg2["enabled"] is False
        assert len(cfg2["fields"]) == 1
        assert cfg2["fields"][0]["name"] == "year"
        assert cfg2["fields"][0]["type"] == "time"