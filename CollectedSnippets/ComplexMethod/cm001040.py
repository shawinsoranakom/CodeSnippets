def test_excluded_block_types_contains_expected_types(self):
        """Verify COPILOT_EXCLUDED_BLOCK_TYPES contains all graph-only types."""
        assert BlockType.INPUT in COPILOT_EXCLUDED_BLOCK_TYPES
        assert BlockType.OUTPUT in COPILOT_EXCLUDED_BLOCK_TYPES
        assert BlockType.WEBHOOK in COPILOT_EXCLUDED_BLOCK_TYPES
        assert BlockType.WEBHOOK_MANUAL in COPILOT_EXCLUDED_BLOCK_TYPES
        assert BlockType.NOTE in COPILOT_EXCLUDED_BLOCK_TYPES
        assert BlockType.HUMAN_IN_THE_LOOP in COPILOT_EXCLUDED_BLOCK_TYPES
        assert BlockType.AGENT in COPILOT_EXCLUDED_BLOCK_TYPES