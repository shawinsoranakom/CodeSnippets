def test_config_hash(self):
        config = torch._dynamo.config
        starting_hash = config.get_hash()

        with config.patch({"verbose": not config.verbose}):
            new_hash = config.get_hash()
            if "verbose" not in config._compile_ignored_keys:
                raise AssertionError("Expected 'verbose' in _compile_ignored_keys")
            if new_hash != starting_hash:
                raise AssertionError(
                    f"Expected hash to remain {starting_hash}, got {new_hash}"
                )

        new_hash = config.get_hash()
        if new_hash != starting_hash:
            raise AssertionError(
                f"Expected hash to remain {starting_hash}, got {new_hash}"
            )

        with config.patch({"suppress_errors": not config.suppress_errors}):
            changed_hash = config.get_hash()
            if "suppress_errors" in config._compile_ignored_keys:
                raise AssertionError(
                    "Expected 'suppress_errors' not in _compile_ignored_keys"
                )
            if changed_hash == starting_hash:
                raise AssertionError(
                    f"Expected hash to change from {starting_hash}, got {changed_hash}"
                )

            # Test nested patch
            with config.patch({"verbose": not config.verbose}):
                inner_changed_hash = config.get_hash()
                if inner_changed_hash != changed_hash:
                    raise AssertionError(
                        f"Expected inner hash {inner_changed_hash} to equal {changed_hash}"
                    )
                if inner_changed_hash == starting_hash:
                    raise AssertionError(
                        f"Expected inner hash {inner_changed_hash} to differ from starting {starting_hash}"
                    )

        newest_hash = config.get_hash()
        if changed_hash == newest_hash:
            raise AssertionError(
                f"Expected changed_hash {changed_hash} to differ from newest_hash {newest_hash}"
            )
        if newest_hash != starting_hash:
            raise AssertionError(
                f"Expected newest_hash {newest_hash} to equal starting_hash {starting_hash}"
            )