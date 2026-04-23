def _run_both_exist_block(
        self, is_model, is_peft, supports_llama32, model_name, is_local_dir = False
    ):
        """Simulate the both_exist detection block from loader.py.

        This mirrors the exact logic at lines 500-517 / 1276-1292 of loader.py.
        Returns (both_exist, glob_called).
        """
        from unittest.mock import MagicMock

        both_exist = (is_model and is_peft) and not supports_llama32
        glob_mock = MagicMock(
            return_value = [
                f"{model_name}/config.json",
                f"{model_name}/adapter_config.json",
            ]
        )

        # This mirrors the guarded block in loader.py
        if supports_llama32 and is_model and is_peft:
            if is_local_dir:
                # Local path branch — would use os.path.exists in real code
                both_exist = True  # simulate both files present locally
            else:
                files = glob_mock(f"{model_name}/*.json")
                files = list(os.path.split(x)[-1] for x in files)
                if (
                    sum(x == "adapter_config.json" or x == "config.json" for x in files)
                    >= 2
                ):
                    both_exist = True

        return both_exist, glob_mock.called