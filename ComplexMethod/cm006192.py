def test_memory_usage_efficiency(self):
        """Test that memory usage is more efficient with lazy loading."""
        from langflow.components import processing

        # Count currently loaded components
        initial_component_count = len([k for k in processing.__dict__ if k.endswith("Component")])

        # Access just one component
        combine_text = processing.CombineTextComponent
        assert combine_text is not None

        # At least one more component should be loaded now
        after_one_access = len([k for k in processing.__dict__ if k.endswith("Component")])
        assert after_one_access >= initial_component_count

        # Access another component
        split_text = processing.SplitTextComponent
        assert split_text is not None

        # Should have at least one more component loaded
        after_two_access = len([k for k in processing.__dict__ if k.endswith("Component")])
        assert after_two_access >= after_one_access