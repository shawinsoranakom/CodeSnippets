async def _run_live_concurrency_iteration(self, *, iteration: int) -> list[ScenarioResult]:
        results: list[ScenarioResult] = []

        print(f"[cc/{iteration}.1] cc_create_same_prefix_race")
        shared_prefix = f"e2e_cc_shared_{uuid4().hex[:6]}_"
        shared_dep_name = self._mk_name("dep_cc_shared")
        shared_cfg_name = self._mk_name("cfg_cc_shared")
        shared_snap_name = self._mk_name("snap_cc_shared")
        shared_payload = self._build_create_payload(
            tool_payloads=[self._build_flow_payload(label="cc_shared_snap", name_override=shared_snap_name)],
            raw_connection=DeploymentConfig(
                name=shared_cfg_name,
                description="concurrency create collision",
                environment_variables={},
            ),
            resource_name_prefix=shared_prefix,
        )
        shared_payload.spec = shared_payload.spec.model_copy(update={"name": shared_dep_name}, deep=True)
        create_race = await self._run_parallel_calls(
            {
                "left": lambda: self._run_create(shared_payload.model_copy(deep=True)),
                "right": lambda: self._run_create(shared_payload.model_copy(deep=True)),
            }
        )
        left_status, left_detail, left_created = create_race["left"]
        right_status, right_detail, right_created = create_race["right"]
        self._track_created_result(left_created)
        self._track_created_result(right_created)
        create_pair = (left_status, right_status)
        create_pair_ok = create_pair in {
            (OUTCOME_SUCCESS, OUTCOME_CONFLICT),
            (OUTCOME_CONFLICT, OUTCOME_SUCCESS),
            (OUTCOME_SUCCESS, OUTCOME_SUCCESS),
        }
        create_no_internal = OUTCOME_FAILURE not in {left_status, right_status}
        results.append(
            self._build_result(
                name="cc_create_same_prefix_race",
                expected={OUTCOME_SUCCESS, OUTCOME_CONFLICT},
                actual_outcome=max(left_status, right_status),
                detail=f"left={left_status}:{left_detail} right={right_status}:{right_detail}",
                ok=create_pair_ok and create_no_internal,
            )
        )

        print(f"[cc/{iteration}.2] cc_update_spec_vs_snapshot_race")
        primary_id, _primary_cfg_id, _primary_snaps, _ = await self._create_update_seed(
            label=f"cc_upd_primary_{iteration}",
            snapshot_count=2,
        )
        _donor_id, donor_cfg_id, donor_snapshot_ids, _ = await self._create_update_seed(
            label=f"cc_upd_donor_{iteration}",
            snapshot_count=1,
        )
        donor_snapshot_id = next(iter(donor_snapshot_ids), "")
        update_race = await self._run_parallel_calls(
            {
                "spec": lambda: self._run_update(
                    primary_id,
                    DeploymentUpdate(spec=BaseDeploymentDataUpdate(description="cc concurrent spec update")),
                ),
                "snapshot": lambda: self._run_update(
                    primary_id,
                    DeploymentUpdate(
                        provider_data={
                            "tools": {},
                            "connections": {"existing_app_ids": [str(donor_cfg_id)]},
                            "operations": [
                                {
                                    "op": "bind",
                                    "tool": self._make_tool_id_with_ref(donor_snapshot_id),
                                    "app_ids": [str(donor_cfg_id)],
                                }
                            ],
                        }
                    ),
                ),
            }
        )
        spec_status, spec_detail, _ = update_race["spec"]
        snapshot_status, snapshot_detail, _ = update_race["snapshot"]
        list_status, _list_detail, list_after = await self._run_list_snapshots(primary_id)
        attached_after = self._extract_snapshot_ids(list_after)
        no_internal_race = OUTCOME_FAILURE not in {spec_status, snapshot_status}
        results.append(
            self._build_result(
                name="cc_update_spec_vs_snapshot_race",
                expected={
                    OUTCOME_SUCCESS,
                    OUTCOME_INVALID_OPERATION,
                    OUTCOME_CONFLICT,
                    OUTCOME_INVALID_CONTENT,
                    OUTCOME_NOT_FOUND,
                },
                actual_outcome=max(spec_status, snapshot_status),
                detail=f"spec={spec_status}:{spec_detail} snapshot={snapshot_status}:{snapshot_detail}",
                ok=(
                    no_internal_race
                    and list_status == OUTCOME_SUCCESS
                    and self._has_unique_snapshot_ids(attached_after)
                ),
            )
        )

        print(f"[cc/{iteration}.3] cc_update_vs_delete_deployment_race")
        race_delete_id, _race_delete_cfg, _race_delete_snaps, _ = await self._create_update_seed(
            label=f"cc_upd_del_{iteration}",
            snapshot_count=1,
        )
        update_delete_race = await self._run_parallel_calls(
            {
                "update": lambda: self._run_update(
                    race_delete_id,
                    DeploymentUpdate(spec=BaseDeploymentDataUpdate(description="cc update while delete")),
                ),
                "delete": lambda: self._run_delete(race_delete_id),
            }
        )
        upd_status, upd_detail, _ = update_delete_race["update"]
        del_status, del_detail, _ = update_delete_race["delete"]
        status_after_delete_race, _status_detail, _status_payload = await self._run_status(race_delete_id)
        allowed_pairs = {
            (OUTCOME_SUCCESS, OUTCOME_SUCCESS),
            (OUTCOME_NOT_FOUND, OUTCOME_SUCCESS),
            (OUTCOME_SUCCESS, OUTCOME_NOT_FOUND),
            (OUTCOME_NOT_FOUND, OUTCOME_NOT_FOUND),
        }
        results.append(
            self._build_result(
                name="cc_update_vs_delete_deployment_race",
                expected={OUTCOME_SUCCESS, OUTCOME_NOT_FOUND, OUTCOME_FAILURE},
                actual_outcome=max(upd_status, del_status),
                detail=(
                    f"update={upd_status}:{upd_detail} "
                    f"delete={del_status}:{del_detail} status={status_after_delete_race}"
                ),
                ok=(upd_status, del_status) in allowed_pairs
                or (
                    OUTCOME_FAILURE in {upd_status, del_status} and "not found" in f"{upd_detail} {del_detail}".lower()
                ),
            )
        )
        self.created_deployment_ids.discard(race_delete_id)

        print(f"[cc/{iteration}.4] cc_execution_vs_delete_deployment_race")
        exec_delete_id, _exec_delete_cfg, _exec_delete_snapshots, _ = await self._create_update_seed(
            label=f"cc_exec_del_{iteration}",
            snapshot_count=1,
        )
        exec_delete_race = await self._run_parallel_calls(
            {
                "execution": lambda: self._run_create_execution(
                    exec_delete_id,
                    provider_data={"message": {"role": "user", "content": "woah"}},
                ),
                "delete": lambda: self._run_delete(exec_delete_id),
            }
        )
        exec_status, exec_detail, _ = exec_delete_race["execution"]
        del_exec_status, del_exec_detail, _ = exec_delete_race["delete"]
        results.append(
            self._build_result(
                name="cc_execution_vs_delete_deployment_race",
                expected={OUTCOME_SUCCESS, OUTCOME_NOT_FOUND, OUTCOME_SUCCESS, OUTCOME_FAILURE},
                actual_outcome=max(exec_status, del_exec_status),
                detail=f"execution={exec_status}:{exec_detail} delete={del_exec_status}:{del_exec_detail}",
                ok=OUTCOME_FAILURE not in {exec_status, del_exec_status}
                or "not found" in f"{exec_detail} {del_exec_detail}".lower(),
            )
        )
        self.created_deployment_ids.discard(exec_delete_id)

        print(f"[cc/{iteration}.5] cc_delete_snapshot_during_update_bindings")
        delete_bind_id, bind_cfg_id, bind_snapshot_ids, _ = await self._create_update_seed(
            label=f"cc_del_bind_{iteration}",
            snapshot_count=2,
        )
        delete_target_snapshot_id = next(iter(bind_snapshot_ids), "")

        async def _delete_target_before_bind(*args: Any, **kwargs: Any) -> None:  # noqa: ARG001
            clients = kwargs.get("clients")
            existing_tool_deltas = kwargs.get("existing_tool_deltas") or {}
            target_ids = list(existing_tool_deltas.keys())
            tool_id = str(target_ids[0]) if target_ids else delete_target_snapshot_id
            if clients and tool_id:
                await self._safe_delete_snapshot(clients=clients, snapshot_id=tool_id)

        del_bind_status, del_bind_detail, _ = await self._run_with_stage_hook(
            stage="update_bindings",
            operation=lambda: self._run_update(
                delete_bind_id,
                DeploymentUpdate(
                    provider_data={
                        "tools": {},
                        "connections": {"existing_app_ids": [str(bind_cfg_id)]},
                        "operations": [
                            {
                                "op": "unbind",
                                "tool": self._make_tool_ref(tool_id),
                                "app_ids": [str(bind_cfg_id)],
                            }
                            for tool_id in sorted(bind_snapshot_ids)
                        ],
                    }
                ),
            ),
            hook_before=_delete_target_before_bind,
        )
        results.append(
            self._build_result(
                name="cc_delete_snapshot_during_update_bindings",
                expected={OUTCOME_INVALID_CONTENT, OUTCOME_INVALID_OPERATION, OUTCOME_SUCCESS},
                actual_outcome=del_bind_status,
                detail=del_bind_detail,
                ok=del_bind_status in {OUTCOME_SUCCESS, OUTCOME_INVALID_OPERATION, OUTCOME_INVALID_CONTENT},
            )
        )

        print(f"[cc/{iteration}.6] cc_delete_config_after_update_raw_create")
        delete_cfg_id, _delete_cfg_base_id, delete_cfg_snapshots, _ = await self._create_update_seed(
            label=f"cc_del_cfg_{iteration}",
            snapshot_count=1,
        )
        target_tool_id = next(iter(delete_cfg_snapshots), "")
        if not target_tool_id:
            results.append(
                self._build_result(
                    name="cc_delete_config_after_update_raw_create",
                    expected={OUTCOME_INVALID_OPERATION, OUTCOME_INVALID_CONTENT, OUTCOME_CONFLICT, OUTCOME_FAILURE},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed snapshot id missing for update raw config stage",
                    ok=False,
                )
            )
            return results
        cfg_prefix = f"e2e_cc_del_cfg_{uuid4().hex[:6]}_"
        raw_cfg_name = self._mk_name("cc_raw_cfg")

        async def _delete_created_app_after_config_create(created_app_id: Any, **kwargs: Any) -> None:
            if not created_app_id:
                created_app_id = kwargs.get("app_id")
            app_id = str(created_app_id or "").strip()
            clients = await self.service._get_provider_clients(user_id=self.user_id, db=self.db)  # noqa: SLF001
            if app_id:
                await self._safe_delete_config(clients=clients, config_id=app_id)

        del_cfg_status, del_cfg_detail, _ = await self._run_with_stage_hook(
            stage="update_create_config",
            operation=lambda: self._run_update(
                delete_cfg_id,
                DeploymentUpdate(
                    provider_data={
                        "resource_name_prefix": cfg_prefix,
                        "tools": {},
                        "connections": {"raw_payloads": [{"app_id": raw_cfg_name, "environment_variables": {}}]},
                        "operations": [
                            {
                                "op": "bind",
                                "tool": self._make_tool_id_with_ref(target_tool_id),
                                "app_ids": [raw_cfg_name],
                            }
                        ],
                    }
                ),
            ),
            hook_after=_delete_created_app_after_config_create,
        )
        results.append(
            self._build_result(
                name="cc_delete_config_after_update_raw_create",
                expected={OUTCOME_INVALID_OPERATION, OUTCOME_INVALID_CONTENT, OUTCOME_CONFLICT, OUTCOME_FAILURE},
                actual_outcome=del_cfg_status,
                detail=del_cfg_detail,
                ok=del_cfg_status
                in {
                    OUTCOME_INVALID_OPERATION,
                    OUTCOME_INVALID_CONTENT,
                    OUTCOME_CONFLICT,
                    OUTCOME_FAILURE,
                },
            )
        )

        print(f"[cc/{iteration}.7] cc_create_during_create_snapshots_stage")
        create_race_prefix = f"e2e_cc_create_stage_{uuid4().hex[:6]}_"
        create_race_dep = self._mk_name("cc_stage_dep")
        create_race_cfg = self._mk_name("cc_stage_cfg")
        create_race_snap = self._mk_name("cc_stage_snap")
        race_payload = self._build_create_payload(
            tool_payloads=[self._build_flow_payload(label="cc_stage_snap", name_override=create_race_snap)],
            raw_connection=DeploymentConfig(
                name=create_race_cfg,
                description="cc competing create",
                environment_variables={},
            ),
            resource_name_prefix=create_race_prefix,
        )
        race_payload.spec = race_payload.spec.model_copy(update={"name": create_race_dep}, deep=True)
        competing_create_task: asyncio.Task[tuple[str, str, WxoCreatedDeploymentResult | None]] | None = None

        async def _launch_competing_create(*args: Any, **kwargs: Any) -> None:  # noqa: ARG001
            nonlocal competing_create_task
            if competing_create_task is None:
                competing_create_task = asyncio.create_task(self._run_create(race_payload.model_copy(deep=True)))
                await asyncio.sleep(0)

        staged_create_status, staged_create_detail, staged_create_created = await self._run_with_stage_hook(
            stage="create_snapshots",
            operation=lambda: self._run_create(race_payload.model_copy(deep=True)),
            hook_before=_launch_competing_create,
        )
        competing_create_result = (OUTCOME_FAILURE, "competing create did not start", None)
        if competing_create_task is not None:
            competing_create_result = await competing_create_task
        comp_status, comp_detail, comp_created = competing_create_result
        self._track_created_result(staged_create_created)
        self._track_created_result(comp_created)
        staged_pair = (staged_create_status, comp_status)
        results.append(
            self._build_result(
                name="cc_create_during_create_snapshots_stage",
                expected={OUTCOME_SUCCESS, OUTCOME_CONFLICT},
                actual_outcome=max(staged_create_status, comp_status),
                detail=f"main={staged_create_status}:{staged_create_detail} competing={comp_status}:{comp_detail}",
                ok=(
                    staged_pair
                    in {
                        (OUTCOME_SUCCESS, OUTCOME_CONFLICT),
                        (OUTCOME_CONFLICT, OUTCOME_SUCCESS),
                        (OUTCOME_SUCCESS, OUTCOME_SUCCESS),
                    }
                    and OUTCOME_FAILURE not in staged_pair
                ),
            )
        )

        print(f"[cc/{iteration}.8] cc_create_during_update_raw_config_stage")
        update_create_id, _update_create_cfg, update_create_snaps, _ = await self._create_update_seed(
            label=f"cc_create_update_cfg_{iteration}",
            snapshot_count=1,
        )
        update_target_tool_id = next(iter(update_create_snaps), "")
        if not update_target_tool_id:
            results.append(
                self._build_result(
                    name="cc_create_during_update_raw_config_stage",
                    expected={OUTCOME_SUCCESS, OUTCOME_CONFLICT},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed snapshot id missing for competing update",
                    ok=False,
                )
            )
            return results
        update_cfg_prefix = f"e2e_cc_upd_cfg_create_{uuid4().hex[:6]}_"
        update_cfg_name = self._mk_name("cc_upd_cfg_create")
        competing_update_task: asyncio.Task[tuple[str, str, Any | None]] | None = None

        competing_update_payload = DeploymentUpdate(
            provider_data={
                "resource_name_prefix": update_cfg_prefix,
                "tools": {},
                "connections": {"raw_payloads": [{"app_id": update_cfg_name, "environment_variables": {}}]},
                "operations": [
                    {
                        "op": "bind",
                        "tool": self._make_tool_id_with_ref(update_target_tool_id),
                        "app_ids": [update_cfg_name],
                    }
                ],
            },
        )

        async def _launch_competing_update_create(*args: Any, **kwargs: Any) -> None:  # noqa: ARG001
            nonlocal competing_update_task
            if competing_update_task is None:
                competing_update_task = asyncio.create_task(
                    self._run_update(update_create_id, competing_update_payload.model_copy(deep=True))
                )
                await asyncio.sleep(0)

        update_cfg_status, update_cfg_detail, _ = await self._run_with_stage_hook(
            stage="update_create_config",
            operation=lambda: self._run_update(update_create_id, competing_update_payload.model_copy(deep=True)),
            hook_before=_launch_competing_update_create,
        )
        competing_update_result = (OUTCOME_FAILURE, "competing update did not start", None)
        if competing_update_task is not None:
            competing_update_result = await competing_update_task
        competing_upd_status, competing_upd_detail, _ = competing_update_result
        results.append(
            self._build_result(
                name="cc_create_during_update_raw_config_stage",
                expected={OUTCOME_SUCCESS, OUTCOME_CONFLICT},
                actual_outcome=max(update_cfg_status, competing_upd_status),
                detail=(
                    f"main={update_cfg_status}:{update_cfg_detail} "
                    f"competing={competing_upd_status}:{competing_upd_detail}"
                ),
                ok=OUTCOME_FAILURE not in {update_cfg_status, competing_upd_status},
            )
        )

        print(f"[cc/{iteration}.9] cc_delete_resources_during_update_rollback")
        rollback_id, rollback_cfg_id, rollback_seed_snapshots, _ = await self._create_update_seed(
            label=f"cc_rollback_delete_{iteration}",
            snapshot_count=1,
        )
        if not rollback_cfg_id:
            results.append(
                self._build_result(
                    name="cc_delete_resources_during_update_rollback",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed rollback config id missing",
                    ok=False,
                )
            )
            return results
        rollback_seed_tool_id = next(iter(rollback_seed_snapshots), "")
        if not rollback_seed_tool_id:
            results.append(
                self._build_result(
                    name="cc_delete_resources_during_update_rollback",
                    expected={OUTCOME_FAILURE},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed snapshot id missing for rollback race",
                    ok=False,
                )
            )
            return results
        rollback_prefix = f"e2e_cc_rollback_{uuid4().hex[:6]}_"
        rollback_raw_flow = self._build_flow_payload(label=f"cc_rb_raw_{iteration}")
        rollback_raw_cfg_name = self._mk_name("cc_rb_cfg")
        rollback_status, rollback_detail, _ = await self._run_with_stage_hook(
            stage="update_rollback_resources",
            operation=lambda: self._run_update(
                rollback_id,
                DeploymentUpdate(
                    spec=BaseDeploymentDataUpdate(description="cc rollback delete race"),
                    provider_data={
                        "resource_name_prefix": rollback_prefix,
                        "tools": {
                            "raw_payloads": [rollback_raw_flow.model_dump(mode="json")],
                        },
                        "connections": {
                            "existing_app_ids": [str(rollback_cfg_id)],
                            "raw_payloads": [{"app_id": rollback_raw_cfg_name, "environment_variables": {}}],
                        },
                        "operations": [
                            {
                                "op": "unbind",
                                "tool": self._make_tool_ref(rollback_seed_tool_id),
                                "app_ids": [str(rollback_cfg_id)],
                            },
                            {
                                "op": "bind",
                                "tool": {"name_of_raw": rollback_raw_flow.name},
                                "app_ids": [rollback_raw_cfg_name],
                            },
                        ],
                    },
                ),
                inject={
                    "update_bindings": {
                        "fail_first_n": 1,
                        "error_type": "runtime",
                        "message": "cc_rollback_trigger",
                    }
                },
            ),
            hook_before=self._delete_resources_before_rollback_hook,
        )
        results.append(
            self._build_result(
                name="cc_delete_resources_during_update_rollback",
                expected={OUTCOME_FAILURE},
                actual_outcome=rollback_status,
                detail=rollback_detail,
                ok=rollback_status == OUTCOME_FAILURE,
            )
        )

        print(f"[cc/{iteration}.10] cc_create_during_update_rollback")
        rollback_create_id, rollback_create_cfg_id, rollback_create_snaps, _ = await self._create_update_seed(
            label=f"cc_rollback_create_{iteration}",
            snapshot_count=1,
        )
        if not rollback_create_cfg_id:
            results.append(
                self._build_result(
                    name="cc_create_during_update_rollback",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed rollback-create config id missing",
                    ok=False,
                )
            )
            return results
        rollback_create_seed_tool_id = next(iter(rollback_create_snaps), "")
        if not rollback_create_seed_tool_id:
            results.append(
                self._build_result(
                    name="cc_create_during_update_rollback",
                    expected={OUTCOME_FAILURE, OUTCOME_SUCCESS, OUTCOME_CONFLICT},
                    actual_outcome=OUTCOME_FAILURE,
                    detail="seed snapshot id missing for rollback create race",
                    ok=False,
                )
            )
            return results
        rollback_create_prefix = f"e2e_cc_rb_create_{uuid4().hex[:6]}_"
        rollback_create_cfg_name = self._mk_name("cc_rb_create_cfg")
        competing_rollback_create_task: asyncio.Task[tuple[str, str, Any | None]] | None = None

        async def _launch_competing_create_before_rollback(*args: Any, **kwargs: Any) -> None:  # noqa: ARG001
            nonlocal competing_rollback_create_task
            if competing_rollback_create_task is not None:
                return
            competing_rollback_create_task = asyncio.create_task(
                self._run_update(
                    rollback_create_id,
                    DeploymentUpdate(
                        provider_data={
                            "resource_name_prefix": rollback_create_prefix,
                            "tools": {},
                            "connections": {
                                "raw_payloads": [{"app_id": rollback_create_cfg_name, "environment_variables": {}}]
                            },
                            "operations": [
                                {
                                    "op": "bind",
                                    "tool": self._make_tool_id_with_ref(rollback_create_seed_tool_id),
                                    "app_ids": [rollback_create_cfg_name],
                                }
                            ],
                        },
                    ),
                )
            )
            await asyncio.sleep(0)

        rollback_create_raw_flow = self._build_flow_payload(label=f"cc_rb_create_raw_{iteration}")
        rollback_create_status, rollback_create_detail, _ = await self._run_with_stage_hook(
            stage="update_rollback_resources",
            operation=lambda: self._run_update(
                rollback_create_id,
                DeploymentUpdate(
                    spec=BaseDeploymentDataUpdate(description="cc rollback create race"),
                    provider_data={
                        "resource_name_prefix": rollback_create_prefix,
                        "tools": {
                            "raw_payloads": [rollback_create_raw_flow.model_dump(mode="json")],
                        },
                        "connections": {
                            "existing_app_ids": [str(rollback_create_cfg_id)],
                            "raw_payloads": [{"app_id": rollback_create_cfg_name, "environment_variables": {}}],
                        },
                        "operations": [
                            {
                                "op": "unbind",
                                "tool": self._make_tool_ref(rollback_create_seed_tool_id),
                                "app_ids": [str(rollback_create_cfg_id)],
                            },
                            {
                                "op": "bind",
                                "tool": {"name_of_raw": rollback_create_raw_flow.name},
                                "app_ids": [rollback_create_cfg_name],
                            },
                        ],
                    },
                ),
                inject={
                    "update_bindings": {
                        "fail_first_n": 1,
                        "error_type": "runtime",
                        "message": "cc_rollback_create_trigger",
                    }
                },
            ),
            hook_before=_launch_competing_create_before_rollback,
        )
        competing_rollback_create_result = (OUTCOME_FAILURE, "competing rollback create missing", None)
        if competing_rollback_create_task is not None:
            competing_rollback_create_result = await competing_rollback_create_task
        comp_rb_status, comp_rb_detail, _ = competing_rollback_create_result
        results.append(
            self._build_result(
                name="cc_create_during_update_rollback",
                expected={OUTCOME_FAILURE, OUTCOME_SUCCESS, OUTCOME_CONFLICT},
                actual_outcome=max(rollback_create_status, comp_rb_status),
                detail=(
                    f"main={rollback_create_status}:{rollback_create_detail} "
                    f"competing={comp_rb_status}:{comp_rb_detail}"
                ),
                ok=rollback_create_status == OUTCOME_FAILURE
                and comp_rb_status in {OUTCOME_SUCCESS, OUTCOME_CONFLICT, OUTCOME_FAILURE},
            )
        )

        print(f"[cc/{iteration}.11] cc_parallel_updates_isolation")
        dep_a, cfg_a, _snap_a, _ = await self._create_update_seed(label=f"cc_iso_a_{iteration}", snapshot_count=1)
        dep_b, cfg_b, _snap_b, _ = await self._create_update_seed(label=f"cc_iso_b_{iteration}", snapshot_count=1)
        isolation_race = await self._run_parallel_calls(
            {
                "a": lambda: self._run_update(
                    dep_a,
                    DeploymentUpdate(spec=BaseDeploymentDataUpdate(description="isolation-a")),
                ),
                "b": lambda: self._run_update(
                    dep_b,
                    DeploymentUpdate(spec=BaseDeploymentDataUpdate(description="isolation-b")),
                ),
            }
        )
        iso_a_status, iso_a_detail, _ = isolation_race["a"]
        iso_b_status, iso_b_detail, _ = isolation_race["b"]
        cfg_list_a_status, _cfg_a_detail, cfg_list_a = await self._run_list_configs(dep_a)
        cfg_list_b_status, _cfg_b_detail, cfg_list_b = await self._run_list_configs(dep_b)
        cfg_ids_a = self._extract_config_ids(cfg_list_a)
        cfg_ids_b = self._extract_config_ids(cfg_list_b)
        print(
            "[cc/debug] parallel_updates_isolation "
            f"dep_a={dep_a} cfg_a={cfg_a} update_a={iso_a_status}:{iso_a_detail} "
            f"list_a={cfg_list_a_status}:{_cfg_a_detail} cfg_ids_a={sorted(cfg_ids_a)} "
            f"dep_b={dep_b} cfg_b={cfg_b} update_b={iso_b_status}:{iso_b_detail} "
            f"list_b={cfg_list_b_status}:{_cfg_b_detail} cfg_ids_b={sorted(cfg_ids_b)}"
        )
        isolation_ok = (
            cfg_list_a_status == OUTCOME_SUCCESS and cfg_list_b_status == OUTCOME_SUCCESS and cfg_ids_a and cfg_ids_b
        )
        if cfg_a:
            isolation_ok = isolation_ok and str(cfg_a) in cfg_ids_a
        if cfg_b:
            isolation_ok = isolation_ok and str(cfg_b) in cfg_ids_b
        results.append(
            self._build_result(
                name="cc_parallel_updates_isolation",
                expected={OUTCOME_SUCCESS},
                actual_outcome=max(iso_a_status, iso_b_status),
                detail=f"a={iso_a_status}:{iso_a_detail} b={iso_b_status}:{iso_b_detail}",
                ok=isolation_ok and iso_a_status == OUTCOME_SUCCESS and iso_b_status == OUTCOME_SUCCESS,
            )
        )
        return results