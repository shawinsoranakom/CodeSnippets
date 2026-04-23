def _aggregate_evaluations(
        self,
        all_samples: list[list[ThoughtEvaluation]],
    ) -> list[ThoughtEvaluation]:
        """Aggregate multiple evaluation samples (from ToT paper).

        For categorical mode, uses majority voting.
        For numeric mode, uses average scores.

        Args:
            all_samples: List of evaluation lists from multiple sampling runs

        Returns:
            Aggregated evaluations
        """
        if not all_samples:
            return []

        if len(all_samples) == 1:
            return all_samples[0]

        num_thoughts = len(all_samples[0])
        aggregated: list[ThoughtEvaluation] = []

        for i in range(num_thoughts):
            if self.config.evaluation_mode == "categorical":
                # Majority voting for categorical
                votes: Counter[str] = Counter()
                for sample in all_samples:
                    cat = sample[i].categorical if i < len(sample) else None
                    if cat is not None:
                        votes[cat] += 1

                if votes:
                    winner = votes.most_common(1)[0][0]
                    vote_count = votes[winner]
                else:
                    winner = "maybe"
                    vote_count = 0

                score_map = {"sure": 10.0, "maybe": 5.0, "impossible": 0.0}
                num_samples = len(all_samples)
                reasoning = f"Majority: {winner} ({vote_count}/{num_samples})"
                aggregated.append(
                    ThoughtEvaluation(
                        thought_index=i,
                        score=score_map.get(winner, 5.0),
                        reasoning=reasoning,
                        is_promising=winner != "impossible",
                        categorical=winner,  # type: ignore[arg-type]
                    )
                )
            else:
                # Average scores for numeric
                scores = [sample[i].score for sample in all_samples if i < len(sample)]
                avg_score = sum(scores) / len(scores) if scores else 5.0

                aggregated.append(
                    ThoughtEvaluation(
                        thought_index=i,
                        score=avg_score,
                        reasoning=f"Average of {len(scores)} samples",
                        is_promising=avg_score >= self.config.min_score_threshold,
                    )
                )

        return aggregated