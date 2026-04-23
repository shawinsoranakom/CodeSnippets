async def _score_skill(self, skill_md, scenarios, evals):
        """Executor runs all scenarios, then scores outputs."""
        all_results = []
        total_passed = 0
        total_checks = 0
        per_eval = {e["id"]: {"passed": 0, "total": 0} for e in evals}

        for sc in scenarios:
            # Executor runs the skill (free-form text)
            output = await self._ask(
                self.executor,
                f"Execute this skill:\n\n{skill_md}\n\nUser request:\n{sc['input']}",
            )
            # Executor scores the output (JSON)
            scoring = await self._ask_json(
                self.executor,
                (
                    f"Evaluate this output against the criteria.\n\n"
                    f"Input: {sc['input']}\n\n"
                    f"Output: {output}\n\n"
                    f"Criteria:\n{json.dumps(evals, indent=2)}\n\n"
                    f"Return JSON: {{\"results\": [{{\"eval_id\": 1, \"passed\": true, \"reason\": \"...\"}}]}}"
                ),
                fallback={"results": []},
            )
            scores = scoring.get("results", []) if isinstance(scoring, dict) else scoring

            for s in scores:
                eid = s.get("eval_id")
                passed = s.get("passed", False)
                if passed:
                    total_passed += 1
                total_checks += 1
                if eid in per_eval:
                    per_eval[eid]["total"] += 1
                    if passed:
                        per_eval[eid]["passed"] += 1
                all_results.append({**s, "scenario_id": sc["id"]})

        return {
            "passed": total_passed,
            "total": total_checks,
            "per_eval": [
                {"eval_id": k, **v, "pass_rate": round(v["passed"] / max(v["total"], 1) * 100, 1)}
                for k, v in per_eval.items()
            ],
            "details": all_results,
        }