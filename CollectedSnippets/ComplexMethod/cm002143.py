def update_missing_keys(self, model, missing_keys: list[str], prefix: str) -> list[str]:
        not_missing_keys = []
        for name, module in model.named_modules():
            if isinstance(module, Int8SymmetricLinear):
                for missing in missing_keys:
                    if (
                        (name in missing or name in f"{prefix}.{missing}")
                        and not missing.endswith(".weight")
                        and not missing.endswith(".bias")
                    ):
                        not_missing_keys.append(missing)
        return [k for k in missing_keys if k not in not_missing_keys]