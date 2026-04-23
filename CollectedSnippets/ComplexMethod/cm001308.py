def generate_comparison_report(
        self,
        all_results: dict[str, list[ChallengeResult]],
        timestamp: datetime,
    ) -> Path:
        """Generate a comparison report across all configurations.

        Args:
            all_results: Dict mapping config_name -> list of results.
            timestamp: Timestamp for the report.

        Returns:
            Path to the comparison report file.
        """
        test_names: set[str] = set()

        comparison = {
            "timestamp": timestamp.isoformat(),
            "configurations": list(all_results.keys()),
            "results": {},
            "test_names": [],
        }

        for config_name, results in all_results.items():
            passed = sum(1 for r in results if r.success)
            total = len(results)
            total_cost = sum(r.cost for r in results)
            total_steps = sum(r.n_steps for r in results)

            comparison["results"][config_name] = {
                "tests_run": total,
                "tests_passed": passed,
                "tests_failed": total - passed,
                "success_rate": (passed / total * 100) if total > 0 else 0,
                "total_cost": total_cost,
                "avg_steps": total_steps / total if total > 0 else 0,
                "test_results": {
                    r.challenge_name: {
                        "success": r.success,
                        "n_steps": r.n_steps,
                        "cost": r.cost,
                        "error": r.error_message,
                        "timed_out": r.timed_out,
                        "steps": [
                            {
                                "step": s.step_num,
                                "tool": s.tool_name,
                                "args": s.tool_args,
                                "result": (
                                    s.result[:500] + "..."
                                    if len(s.result) > 500
                                    else s.result
                                ),
                                "error": s.is_error,
                            }
                            for s in r.steps
                        ],
                    }
                    for r in results
                },
            }
            test_names.update(r.challenge_name for r in results)

        comparison["test_names"] = sorted(test_names)

        filename = f"strategy_comparison_{timestamp.strftime('%Y%m%dT%H%M%S')}.json"
        report_path = self.reports_dir / filename

        with open(report_path, "w") as f:
            json.dump(comparison, f, indent=2)

        return report_path