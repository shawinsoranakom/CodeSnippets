def _cleanup_registry_based_on_opset_version(self) -> None:
        """Pick the implementation with the highest opset version valid until the current opset version."""
        cleaned_functions = {}
        for target_or_name, decomps in self.functions.items():
            # Filter decompositions to only include those with opset_introduced <= opset_version
            decomps = [d for d in decomps if d.opset_introduced <= self.opset_version]

            # Keep only the decomposition with the highest opset_introduced
            if decomps:
                # Find the maximum opset_introduced
                max_opset = max(d.opset_introduced for d in decomps)

                # Keep all decompositions with the maximum opset_introduced
                cleaned_functions[target_or_name] = [
                    d for d in decomps if d.opset_introduced == max_opset
                ]

        self.functions = cleaned_functions