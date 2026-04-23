def test_generate_backward_compatibility_imports(self):
        """Test generating backward compatibility imports dynamically."""
        # Test with a known module that has lfx imports
        test_cases = [("langflow.schema", "lfx.schema"), ("langflow.custom", "lfx.custom")]

        for lf_module, expected_lfx_source in test_cases:
            lfx_symbols = self._get_expected_symbols(expected_lfx_source)
            assert len(lfx_symbols) > 0, f"Should find some symbols in {expected_lfx_source}"

            # Test that symbols explicitly re-exported by langflow module are accessible
            lf_module_obj = importlib.import_module(lf_module)

            # Get the symbols that langflow explicitly re-exports (from its __all__)
            if hasattr(lf_module_obj, "__all__"):
                lf_reexported = lf_module_obj.__all__
                # Check that these re-exported symbols are actually available
                available_symbols = [sym for sym in lf_reexported if hasattr(lf_module_obj, sym)]
                assert len(available_symbols) > 0, f"Module {lf_module} should have symbols from its __all__"

                # Verify that at least some of the re-exported symbols come from lfx
                lfx_sourced = [sym for sym in available_symbols if sym in lfx_symbols]
                assert len(lfx_sourced) > 0, (
                    f"Module {lf_module} should re-export some symbols from {expected_lfx_source}"
                )
            else:
                # If no __all__, just check that some lfx symbols are accessible
                available_symbols = [sym for sym in lfx_symbols[:10] if hasattr(lf_module_obj, sym)]
                assert len(available_symbols) > 0, (
                    f"Module {lf_module} should have some symbols from {expected_lfx_source}"
                )