def get_top_k_choices(
        self, top_k: int, always_included: list[str] | None = None
    ) -> list[Choice] | None:
        if not self.satisfies_precondition():
            return None
        if torch._inductor.config.use_autoheuristic(self.name):
            if self.augment_context is not None:
                self.context.apply_operations(self.augment_context)
            controller = LearnedHeuristicController(
                self.metadata,
                self.context,
            )
            choices = controller.get_decisions_ranked(top_k)
            if choices is None:
                return None
            if always_included is not None:
                for choice in always_included:
                    if choice not in choices:
                        choices.append(choice)
            return choices
        return None