def __init__(self, source_patterns: str | list[str], target_patterns: str | list[str]):
        self.source_patterns: list[str] = source_patterns
        self.target_patterns: list[str] = target_patterns
        # Those are needed to be able to reverse correctly the transform, as the patterns may be processed
        self._original_source_patterns = self.source_patterns.copy()
        self._original_target_patterns = self.target_patterns.copy()

        # Init fields that will be used during conversion
        self.distributed_operation: TensorParallelLayer | None = None
        self.quantization_operation: ConversionOps | None = None
        self.collected_tensors: dict[str, list[Future]] = defaultdict(list)
        self.layer_targets: dict[str, set[str]] = defaultdict(set)

        # Flag to notice if the Transform was used
        self._was_used = False

        # We need to process a few exceptions here when instantiating the reverse mapping (i.e. the targets become
        # sources, and sources become targets). The issues lie in the sources usually, so here we need to check the
        # targets for the reversed mapping

        # Process target_patterns: detect capturing groups and replace with \1
        # Store the original capturing group patterns for reverse mapping
        target_capturing_groups: list[str] = []
        for i, pattern in enumerate(self.target_patterns):
            self.target_patterns[i], captured_group = process_target_pattern(pattern)
            if captured_group is not None:
                target_capturing_groups.append(captured_group)

        # Validate that we only have one unique capturing group pattern across all targets
        # This ensures deterministic reverse mapping when sources have \1 backreferences
        unique_capturing_groups = set(target_capturing_groups)
        if len(unique_capturing_groups) > 1:
            raise ValueError(
                f"Multiple different capturing groups found in target_patterns: {unique_capturing_groups}. "
                f"All target patterns must use the same capturing group pattern."
            )
        unique_capturing_group = unique_capturing_groups.pop() if unique_capturing_groups else None

        # We also need to check capturing groups in the sources during reverse mapping (e.g. timm_wrapper, sam3)
        for i, pattern in enumerate(self.source_patterns):
            # Replace capturing groups
            if r"\1" in pattern:
                if unique_capturing_group is None:
                    raise ValueError(
                        f"Source pattern '{pattern}' contains \\1 backreference, but no capturing groups "
                        f"found in target_patterns."
                    )
                # Use the unique capturing group from target_patterns for all sources
                pattern = pattern.replace(r"\1", unique_capturing_group, 1)
            # Potentially process a bit more for consistency - only if they are consistent pairs, i.e. the length is the same
            if len(self.source_patterns) == len(self.target_patterns):
                pattern = process_source_pattern(pattern, self._original_target_patterns[i])
            self.source_patterns[i] = pattern

        # Construct the regex we will use to rename keys from the sources to the targets
        branches = []
        for i, source_pattern in enumerate(self.source_patterns):
            group_name = f"g{i}"
            pattern = source_pattern.replace(".*.", r"\..*\.")
            branches.append(f"(?P<{group_name}>{pattern})")
        self.compiled_sources = re.compile("|".join(branches))