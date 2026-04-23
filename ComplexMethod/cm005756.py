async def _run_update_failpoint_scenarios(self) -> list[ScenarioResult]:
        results: list[ScenarioResult] = []
        print("\n[fp-upd] creating seed deployment")
        deployment_id, config_id, snapshot_ids, _ = await self._create_update_seed(
            label="fp_upd_seed",
            snapshot_count=1,
        )
        if not config_id:
            results.append(
                self._build_result(
                    name="fp_update_seed_missing_config",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed deployment config id is missing",
                    ok=False,
                )
            )
            return results
        seed_tool_id = next(iter(snapshot_ids), "")
        if not seed_tool_id:
            results.append(
                self._build_result(
                    name="fp_update_seed_missing_snapshot",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed deployment snapshot id is missing",
                    ok=False,
                )
            )
            return results
        failpoint_prefix = f"e2e_fp_upd_{uuid4().hex[:6]}_"
        failpoint_raw_app_id = self._mk_name("fp_upd_cfg")

        update_payload = DeploymentUpdate(
            spec=BaseDeploymentDataUpdate(description="trigger update failpoint"),
            provider_data={
                "resource_name_prefix": failpoint_prefix,
                "tools": {},
                "connections": {"raw_payloads": [{"app_id": failpoint_raw_app_id, "environment_variables": {}}]},
                "operations": [
                    {
                        "op": "bind",
                        "tool": self._make_tool_id_with_ref(seed_tool_id),
                        "app_ids": [failpoint_raw_app_id],
                    }
                ],
            },
        )

        print("[fp-upd/1] fp_update_bindings_failure_triggers_rollback")
        status_code, detail, _ = await self._run_update(
            deployment_id,
            update_payload,
            inject={
                "update_bindings": {
                    "fail_first_n": 1,
                    "error_type": "runtime",
                    "message": "fp_update_bindings_failure",
                }
            },
        )
        results.append(
            self._build_result(
                name="fp_update_bindings_failure_triggers_rollback",
                expected={OUTCOME_FAILURE},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_FAILURE,
            )
        )

        print("[fp-upd/2] fp_update_bindings_failure_with_rollback_failure")
        status_code, detail, _ = await self._run_update(
            deployment_id,
            update_payload,
            inject={
                "update_bindings": {
                    "fail_first_n": 1,
                    "error_type": "runtime",
                    "message": "fp_update_bindings_failure_again",
                },
                "update_rollback_resources": {
                    "fail_first_n": 1,
                    "error_type": "runtime",
                    "message": "fp_update_rollback_failure",
                },
            },
        )
        results.append(
            self._build_result(
                name="fp_update_bindings_failure_with_rollback_failure",
                expected={OUTCOME_FAILURE},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_FAILURE,
            )
        )

        print("[fp-upd/3] fp_update_failure_then_put_tools_restore")
        restore_id, restore_cfg_id, restore_snaps, _ = await self._create_update_seed(
            label="fp_put_tools_restore",
            snapshot_count=2,
        )
        original_snap_ids = sorted(restore_snaps)
        if not restore_cfg_id or len(original_snap_ids) < MIN_MIXED_SNAPSHOT_IDS:
            results.append(
                self._build_result(
                    name="fp_update_failure_then_put_tools_restore",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=OUTCOME_FAILURE,
                    detail=f"seed insufficient: cfg={restore_cfg_id} snaps={len(original_snap_ids)}",
                    ok=False,
                )
            )
            return results

        restore_prefix = f"e2e_fp_restore_{uuid4().hex[:6]}_"
        restore_raw_cfg = self._mk_name("fp_restore_cfg")
        print("[fp-upd/3a] injecting update failure to corrupt tool list")
        inject_status, inject_detail, _ = await self._run_update(
            restore_id,
            DeploymentUpdate(
                provider_data={
                    "resource_name_prefix": restore_prefix,
                    "tools": {},
                    "connections": {"raw_payloads": [{"app_id": restore_raw_cfg, "environment_variables": {}}]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": self._make_tool_id_with_ref(original_snap_ids[0]),
                            "app_ids": [restore_raw_cfg],
                        }
                    ],
                }
            ),
            inject={
                "update_bindings": {
                    "fail_first_n": 1,
                    "error_type": "runtime",
                    "message": "fp_put_tools_restore_trigger",
                }
            },
        )
        failure_triggered = inject_status == OUTCOME_FAILURE

        print("[fp-upd/3b] restoring via put_tools")
        restore_status, restore_detail, _ = await self._run_update(
            restore_id,
            DeploymentUpdate(provider_data={"put_tools": original_snap_ids}),
        )
        list_status, _list_detail, snap_after_restore = await self._run_list_snapshots(restore_id)
        attached_after_restore = self._extract_snapshot_ids(snap_after_restore)
        restored_ok = set(original_snap_ids) == attached_after_restore
        results.append(
            self._build_result(
                name="fp_update_failure_then_put_tools_restore",
                expected={OUTCOME_SUCCESS},
                actual_outcome=restore_status,
                detail=(
                    f"failure_triggered={failure_triggered} inject={inject_status}:{inject_detail} "
                    f"restore={restore_status}:{restore_detail} "
                    f"attached_after={sorted(attached_after_restore)} expected={original_snap_ids}"
                ),
                ok=(
                    failure_triggered
                    and restore_status == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and restored_ok
                ),
            )
        )

        return results