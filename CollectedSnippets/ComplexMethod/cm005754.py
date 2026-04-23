async def _run_live_update_matrix_scenarios(self) -> list[ScenarioResult]:
        results: list[ScenarioResult] = []
        print("\n[upd] building update matrix seed resources")
        (
            primary_deployment_id,
            _primary_config_id,
            primary_snapshot_ids,
            _,
        ) = await self._create_update_seed(label="upd_primary", snapshot_count=2)
        donor_deployment_id, donor_config_id, donor_snapshot_ids, _ = await self._create_update_seed(
            label="upd_donor",
            snapshot_count=1,
        )
        mixed_donor_deployment_id, _mixed_donor_cfg, mixed_donor_snapshot_ids, _ = await self._create_update_seed(
            label="upd_mixed_donor",
            snapshot_count=1,
        )

        donor_snapshot_id = next(iter(donor_snapshot_ids), "")
        mixed_donor_snapshot_id = next(iter(mixed_donor_snapshot_ids), "")
        removable_snapshot_id = next(iter(primary_snapshot_ids), "")
        retained_snapshot_ids = set(primary_snapshot_ids)
        retained_snapshot_ids.discard(removable_snapshot_id)
        if not donor_config_id:
            results.append(
                self._build_result(
                    name="upd_seed_missing_donor_config",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="donor deployment config id is missing",
                    ok=False,
                )
            )
            return results

        print("[upd/1] upd_spec_only_name_desc")
        updated_name = self._mk_name("dep_upd_spec_only")
        status_code, detail, update_result = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                spec=BaseDeploymentDataUpdate(
                    name=updated_name,
                    description="updated by update matrix spec-only",
                )
            ),
        )
        get_status, _get_detail, get_after_update = await self._run_get(primary_deployment_id)
        spec_ok = bool(get_after_update and getattr(get_after_update, "name", None) == updated_name)
        spec_snapshot_ids_ok = bool(update_result and not getattr(update_result, "snapshot_ids", []))
        results.append(
            self._build_result(
                name="upd_spec_only_name_desc",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and get_status == OUTCOME_SUCCESS
                    and spec_ok
                    and spec_snapshot_ids_ok
                ),
            )
        )

        print("[upd/2] upd_snapshot_remove_only_no_config")
        status_code, detail, remove_result = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {},
                    "operations": [{"op": "remove_tool", "tool": self._make_tool_ref(removable_snapshot_id)}],
                }
            ),
        )
        list_status, _list_detail, list_after_remove = await self._run_list_snapshots(primary_deployment_id)
        attached_after_remove = self._extract_snapshot_ids(list_after_remove)
        remove_snapshot_ids_ok = bool(remove_result and not getattr(remove_result, "snapshot_ids", []))
        results.append(
            self._build_result(
                name="upd_snapshot_remove_only_no_config",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and removable_snapshot_id not in attached_after_remove
                    and retained_snapshot_ids.issubset(attached_after_remove)
                    and remove_snapshot_ids_ok
                ),
            )
        )

        print("[upd/3] upd_config_only_existing_tools_with_config_id")
        retained_snapshot_ids_sorted = sorted(retained_snapshot_ids)
        status_code, detail, config_only_result = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {},
                    "connections": {"existing_app_ids": [str(donor_config_id)]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": self._make_tool_id_with_ref(tool_id),
                            "app_ids": [str(donor_config_id)],
                        }
                        for tool_id in retained_snapshot_ids_sorted
                    ],
                }
            ),
        )
        list_status, _list_detail, list_after_config_only = await self._run_list_snapshots(primary_deployment_id)
        attached_after_config_only = self._extract_snapshot_ids(list_after_config_only)
        config_only_snapshot_ids = self._extract_update_snapshot_ids(config_only_result)
        config_only_snapshot_ids_ok = retained_snapshot_ids.issubset(config_only_snapshot_ids)
        results.append(
            self._build_result(
                name="upd_config_only_existing_tools_with_config_id",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and retained_snapshot_ids.issubset(attached_after_config_only)
                    and config_only_snapshot_ids_ok
                ),
            )
        )

        print("[upd/4] upd_snapshot_add_ids_with_config_id")
        status_code, detail, add_id_result = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {},
                    "connections": {"existing_app_ids": [str(donor_config_id)]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": self._make_tool_id_with_ref(donor_snapshot_id),
                            "app_ids": [str(donor_config_id)],
                        }
                    ],
                }
            ),
        )
        list_status, _list_detail, list_after_add_id = await self._run_list_snapshots(primary_deployment_id)
        attached_after_add_id = self._extract_snapshot_ids(list_after_add_id)
        add_id_snapshot_ids = self._extract_update_snapshot_ids(add_id_result)
        results.append(
            self._build_result(
                name="upd_snapshot_add_ids_with_config_id",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and donor_snapshot_id in attached_after_add_id
                    and donor_snapshot_id in add_id_snapshot_ids
                ),
            )
        )

        print("[upd/5] upd_snapshot_add_raw_with_config_id")
        raw_payload = self._build_flow_payload(label="upd_add_raw")
        status_code, detail, add_raw_result = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "resource_name_prefix": f"e2e_upd_{uuid4().hex[:6]}_",
                    "tools": {"raw_payloads": [raw_payload.model_dump(mode="json")]},
                    "connections": {"existing_app_ids": [str(donor_config_id)]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": {"name_of_raw": raw_payload.name},
                            "app_ids": [str(donor_config_id)],
                        }
                    ],
                }
            ),
        )
        add_raw_snapshot_ids = self._extract_update_snapshot_ids(add_raw_result)
        self.created_snapshot_ids.update(add_raw_snapshot_ids)
        list_status, _list_detail, list_after_add_raw = await self._run_list_snapshots(primary_deployment_id)
        attached_after_add_raw = self._extract_snapshot_ids(list_after_add_raw)
        add_raw_created_ids = add_raw_snapshot_ids
        results.append(
            self._build_result(
                name="upd_snapshot_add_raw_with_config_id",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and bool(add_raw_created_ids)
                    and add_raw_created_ids.issubset(attached_after_add_raw)
                ),
            )
        )

        print("[upd/6] upd_mixed_add_remove_raw_with_config")
        mixed_raw_payload = self._build_flow_payload(label="upd_mixed_raw")
        mixed_remove_id = next(iter(retained_snapshot_ids), "")
        status_code, detail, mixed_result = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "resource_name_prefix": f"e2e_upd_mix_{uuid4().hex[:6]}_",
                    "tools": {
                        "raw_payloads": [mixed_raw_payload.model_dump(mode="json")],
                    },
                    "connections": {"existing_app_ids": [str(donor_config_id)]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": self._make_tool_id_with_ref(mixed_donor_snapshot_id),
                            "app_ids": [str(donor_config_id)],
                        },
                        {"op": "remove_tool", "tool": self._make_tool_ref(mixed_remove_id)},
                        {
                            "op": "bind",
                            "tool": {"name_of_raw": mixed_raw_payload.name},
                            "app_ids": [str(donor_config_id)],
                        },
                    ],
                }
            ),
        )
        mixed_snapshot_ids = self._extract_update_snapshot_ids(mixed_result)
        self.created_snapshot_ids.update(mixed_snapshot_ids)
        list_status, _list_detail, list_after_mixed = await self._run_list_snapshots(primary_deployment_id)
        attached_after_mixed = self._extract_snapshot_ids(list_after_mixed)
        results.append(
            self._build_result(
                name="upd_mixed_add_remove_raw_with_config",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and mixed_remove_id not in attached_after_mixed
                    and mixed_donor_snapshot_id in attached_after_mixed
                    and mixed_donor_snapshot_id in mixed_snapshot_ids
                    and len(mixed_snapshot_ids) >= MIN_MIXED_SNAPSHOT_IDS
                ),
            )
        )

        print("[upd/7] upd_reject_bind_with_undeclared_app_id")
        status_code, detail, _ = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": self._make_tool_id_with_ref(donor_snapshot_id),
                            "app_ids": ["undeclared_app_for_bind"],
                        }
                    ],
                }
            ),
        )
        results.append(
            self._build_result(
                name="upd_reject_bind_with_undeclared_app_id",
                expected={OUTCOME_INVALID_CONTENT},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_INVALID_CONTENT,
            )
        )

        print("[upd/8] upd_reject_raw_bind_with_undeclared_app_id")
        missing_cfg_raw_payload = self._build_flow_payload(label="upd_no_cfg_raw")
        status_code, detail, _ = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {"raw_payloads": [missing_cfg_raw_payload.model_dump(mode="json")]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": {"name_of_raw": missing_cfg_raw_payload.name},
                            "app_ids": ["undeclared_app_for_raw_bind"],
                        }
                    ],
                }
            ),
        )
        results.append(
            self._build_result(
                name="upd_reject_raw_bind_with_undeclared_app_id",
                expected={OUTCOME_INVALID_CONTENT},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_INVALID_CONTENT,
            )
        )

        print("[upd/9] upd_reject_unbind_with_undeclared_app_id")
        status_code, detail, _ = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {},
                    "operations": [
                        {
                            "op": "unbind",
                            "tool": self._make_tool_ref(donor_snapshot_id),
                            "app_ids": ["undeclared_app_for_unbind"],
                        }
                    ],
                }
            ),
        )
        results.append(
            self._build_result(
                name="upd_reject_unbind_with_undeclared_app_id",
                expected={OUTCOME_INVALID_CONTENT},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_INVALID_CONTENT,
            )
        )

        print("[upd/10] upd_reject_unbind_unknown_tool_id")
        status_code, detail, _ = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "connections": {"existing_app_ids": [str(donor_config_id)]},
                    "operations": [
                        {
                            "op": "unbind",
                            "tool": {"source_ref": str(uuid4()), "tool_id": str(uuid4())},
                            "app_ids": [str(donor_config_id)],
                        }
                    ],
                }
            ),
        )
        results.append(
            self._build_result(
                name="upd_reject_unbind_unknown_tool_id",
                expected={OUTCOME_INVALID_CONTENT},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_INVALID_CONTENT,
            )
        )

        print("[upd/11] upd_missing_add_id_fails")
        status_code, detail, _ = await self._run_update(
            primary_deployment_id,
            DeploymentUpdate(
                provider_data={
                    "tools": {},
                    "connections": {"existing_app_ids": [str(donor_config_id)]},
                    "operations": [
                        {
                            "op": "bind",
                            "tool": {"tool_id_with_ref": {"source_ref": str(uuid4()), "tool_id": str(uuid4())}},
                            "app_ids": [str(donor_config_id)],
                        }
                    ],
                }
            ),
        )
        results.append(
            self._build_result(
                name="upd_missing_add_id_fails",
                expected={OUTCOME_INVALID_CONTENT},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_INVALID_CONTENT,
            )
        )

        print("[upd/12] upd_config_raw_payload_conflict")
        conflict_seed_deployment_id, _conflict_cfg_id, _conflict_snapshot_ids, _ = await self._create_update_seed(
            label="upd_conflict_seed",
            snapshot_count=1,
        )
        conflict_suffix = uuid4().hex[:8]
        conflict_prefix = f"e2e_upd_conflict_{conflict_suffix}_"
        conflict_name = f"dup_cfg_{conflict_suffix}"
        conflict_tool_id = next(iter(_conflict_snapshot_ids), "")
        if not conflict_tool_id:
            results.append(
                self._build_result(
                    name="upd_config_raw_payload_conflict",
                    expected={OUTCOME_CONFLICT},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="conflict seed snapshot id is missing",
                    ok=False,
                )
            )
            return results
        conflict_payload = DeploymentUpdate(
            provider_data={
                "resource_name_prefix": conflict_prefix,
                "tools": {},
                "connections": {"raw_payloads": [{"app_id": conflict_name, "environment_variables": {}}]},
                "operations": [
                    {
                        "op": "bind",
                        "tool": self._make_tool_id_with_ref(conflict_tool_id),
                        "app_ids": [conflict_name],
                    }
                ],
            }
        )
        setup_status, _setup_detail, setup_result = await self._run_update(
            conflict_seed_deployment_id, conflict_payload
        )
        setup_created_app_ids = self._extract_update_created_app_ids(setup_result)
        status_code, detail, _ = await self._run_update(conflict_seed_deployment_id, conflict_payload)
        results.append(
            self._build_result(
                name="upd_config_raw_payload_conflict",
                expected={OUTCOME_CONFLICT},
                actual_outcome=status_code,
                detail=(
                    f"setup={setup_status}:{_setup_detail} setup_created_app_ids={sorted(setup_created_app_ids)} "
                    f"conflict={status_code}:{detail}"
                ),
                ok=(
                    setup_status == OUTCOME_SUCCESS and bool(setup_created_app_ids) and status_code == OUTCOME_CONFLICT
                ),
            )
        )

        print("[upd/13] upd_not_found_deployment")
        status_code, detail, _ = await self._run_update(
            str(uuid4()),
            DeploymentUpdate(spec=BaseDeploymentDataUpdate(description="not found update")),
        )
        results.append(
            self._build_result(
                name="upd_not_found_deployment",
                expected={OUTCOME_NOT_FOUND},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_NOT_FOUND,
            )
        )

        print("[upd/14] upd_put_tools_replaces_tool_list")
        put_tools_id, _put_tools_cfg, put_tools_snaps, _ = await self._create_update_seed(
            label="upd_put_tools", snapshot_count=2
        )
        put_tools_sorted = sorted(put_tools_snaps)
        keep_only = [put_tools_sorted[0]]
        status_code, detail, _ = await self._run_update(
            put_tools_id,
            DeploymentUpdate(provider_data={"put_tools": keep_only}),
        )
        list_status, _list_detail, snap_after = await self._run_list_snapshots(put_tools_id)
        attached_after = self._extract_snapshot_ids(snap_after)
        results.append(
            self._build_result(
                name="upd_put_tools_replaces_tool_list",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=f"{detail} | attached_after={sorted(attached_after)} keep_only={keep_only}",
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and attached_after == set(keep_only)
                ),
            )
        )

        print("[upd/15] upd_put_tools_empty_clears_all_tools")
        status_code, detail, _ = await self._run_update(
            put_tools_id,
            DeploymentUpdate(provider_data={"put_tools": []}),
        )
        list_status, _list_detail, snap_after_clear = await self._run_list_snapshots(put_tools_id)
        attached_after_clear = self._extract_snapshot_ids(snap_after_clear)
        results.append(
            self._build_result(
                name="upd_put_tools_empty_clears_all_tools",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=f"{detail} | attached_after={sorted(attached_after_clear)}",
                ok=(
                    status_code == OUTCOME_SUCCESS and list_status == OUTCOME_SUCCESS and len(attached_after_clear) == 0
                ),
            )
        )

        print("[upd/16] upd_put_tools_deduplicates")
        dup_id = put_tools_sorted[0]
        status_code, detail, _ = await self._run_update(
            put_tools_id,
            DeploymentUpdate(provider_data={"put_tools": [dup_id, dup_id, dup_id]}),
        )
        list_status, _list_detail, snap_after_dedup = await self._run_list_snapshots(put_tools_id)
        attached_after_dedup = self._extract_snapshot_ids(snap_after_dedup)
        results.append(
            self._build_result(
                name="upd_put_tools_deduplicates",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=f"{detail} | attached_after={sorted(attached_after_dedup)}",
                ok=(
                    status_code == OUTCOME_SUCCESS
                    and list_status == OUTCOME_SUCCESS
                    and attached_after_dedup == {dup_id}
                ),
            )
        )

        # keep seed deployments tracked for shared final cleanup
        self.created_deployment_ids.add(primary_deployment_id)
        self.created_deployment_ids.add(donor_deployment_id)
        self.created_deployment_ids.add(mixed_donor_deployment_id)
        self.created_deployment_ids.add(put_tools_id)
        return results