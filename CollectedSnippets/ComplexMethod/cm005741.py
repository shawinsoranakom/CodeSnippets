async def _run_scenarios(self, scenarios: list[dict[str, Any]]) -> list[ScenarioResult]:
        results: list[ScenarioResult] = []
        for index, scenario in enumerate(scenarios, start=1):
            print(f"\n[{index}/{len(scenarios)}] {scenario['name']}")
            status_code, detail, created = await self._run_create(scenario["payload"], inject=scenario.get("inject"))
            detail_contains = str(scenario.get("detail_contains") or "").strip()
            detail_ok = not detail_contains or detail_contains in detail
            ok = status_code in scenario["expected"] and detail_ok
            dedupe_expected = scenario.get("assert_dedupe_snapshot_count")
            if dedupe_expected is not None:
                created_snapshot_ids = self._extract_create_snapshot_ids(created.provider_result) if created else set()
                created_snapshot_count = len(created_snapshot_ids)
                dedupe_ok = (
                    status_code == OUTCOME_SUCCESS
                    and created is not None
                    and created_snapshot_count == int(dedupe_expected)
                    and self._has_unique_snapshot_ids(created_snapshot_ids)
                )
                ok = ok and dedupe_ok
                if not dedupe_ok:
                    detail = (
                        f"{detail} | dedupe_check failed: expected_snapshot_count={dedupe_expected} "
                        f"got={created_snapshot_count}"
                    )

            if created:
                self.created_deployment_ids.add(created.deployment_id)
                self.created_snapshot_ids.update(self._extract_create_snapshot_ids(created.provider_result))
                self.created_config_ids.update(self._extract_create_app_ids(created.provider_result))

            results.append(
                ScenarioResult(
                    name=scenario["name"],
                    expected_outcomes=set(scenario["expected"]),
                    actual_outcome=status_code,
                    ok=ok,
                    detail=detail[:600],
                )
            )
        return results