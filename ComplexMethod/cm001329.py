def _process_evaluation(self, content: str) -> None:
        """Process the evaluation phase response."""
        if not self.tree:
            return

        evaluations: list[ThoughtEvaluation] = []

        try:
            # Try to find array in response
            array_match = re.search(r"\[.*\]", content, re.DOTALL)
            if array_match:
                eval_data = json.loads(array_match.group())

                if self.config.evaluation_mode == "categorical":
                    # Parse categorical evaluations
                    for i, e in enumerate(eval_data):
                        if not isinstance(e, dict):
                            continue
                        cat_eval = CategoricalEvaluation(
                            thought_index=e.get("thought_index", i),
                            evaluation=e.get("evaluation", "maybe"),
                            reasoning=e.get("reasoning", ""),
                        )
                        evaluations.append(ThoughtEvaluation.from_categorical(cat_eval))
                else:
                    # Parse numeric evaluations
                    evaluations = [
                        ThoughtEvaluation(
                            thought_index=e.get("thought_index", i),
                            score=float(e.get("score", 0)),
                            reasoning=e.get("reasoning", ""),
                            is_promising=e.get("is_promising", True),
                        )
                        for i, e in enumerate(eval_data)
                        if isinstance(e, dict)
                    ]
        except (json.JSONDecodeError, ValueError):
            # Fallback: assign default scores/categories
            if self.config.evaluation_mode == "categorical":
                evaluations = [
                    ThoughtEvaluation(
                        thought_index=i,
                        score=5.0,
                        reasoning="Default evaluation",
                        is_promising=True,
                        categorical="maybe",
                    )
                    for i in range(len(self.pending_candidates))
                ]
            else:
                evaluations = [
                    ThoughtEvaluation(
                        thought_index=i,
                        score=5.0,
                        reasoning="Default score",
                        is_promising=True,
                    )
                    for i in range(len(self.pending_candidates))
                ]

        self.tree.evaluate_candidates(evaluations)

        # Select best child based on search algorithm
        if self.config.search_algorithm == "dfs":
            # DFS: always go to highest scoring child
            self.tree.select_best_child()
        else:
            # BFS: would maintain a queue of nodes to explore
            # Simplified: just select best for now
            self.tree.select_best_child()