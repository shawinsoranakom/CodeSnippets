def print_final_summary(self) -> None:
        output = {
            "results": {
                config: {
                    "passed": sum(1 for r in results if r.success),
                    "failed": sum(1 for r in results if not r.success),
                    "total": len(results),
                    "cost": sum(r.cost for r in results),
                    "challenges": [
                        {
                            "name": r.challenge_name,
                            "success": r.success,
                            "steps": r.n_steps,
                            "cost": r.cost,
                            "error": r.error_message,
                        }
                        for r in results
                    ],
                }
                for config, results in self.results_by_config.items()
            }
        }
        console.print_json(data=output)