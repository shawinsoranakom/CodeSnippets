async def _run_live_lifecycle_scenarios(self) -> list[ScenarioResult]:
        results: list[ScenarioResult] = []
        print("\n[life/1] live_lifecycle_create_seed")
        status_code, detail, created = await self._run_create(
            self._build_create_payload(
                tool_payloads=[self._build_flow_payload(label="snap_live_lifecycle_seed")],
                raw_connection=self._build_config_payload(label="cfg_live_lifecycle_seed"),
            )
        )
        create_ok = status_code == OUTCOME_SUCCESS and created is not None
        results.append(
            self._build_result(
                name="live_lifecycle_create_seed",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=create_ok,
            )
        )
        if not create_ok or created is None:
            return results

        deployment_id = created.deployment_id
        self.created_deployment_ids.add(deployment_id)
        self.created_snapshot_ids.update(self._extract_create_snapshot_ids(created.provider_result))
        self.created_config_ids.update(self._extract_create_app_ids(created.provider_result))

        print("[life/2] live_list_contains_seed")
        status_code, detail, list_result = await self._run_list(
            params=DeploymentListParams(deployment_ids=[deployment_id])
        )
        list_contains_seed = bool(
            list_result
            and any(str(deployment.id) == deployment_id for deployment in getattr(list_result, "deployments", []))
        )
        results.append(
            self._build_result(
                name="live_list_contains_seed",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_SUCCESS and list_contains_seed,
            )
        )

        print("[life/3] live_get_seed")
        status_code, detail, get_result = await self._run_get(deployment_id)
        got_seed = bool(get_result and str(get_result.id) == deployment_id)
        results.append(
            self._build_result(
                name="live_get_seed",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_SUCCESS and got_seed,
            )
        )

        updated_name = self._mk_name("dep_agent_updated")
        print("[life/4] live_update_seed_name_description")
        status_code, detail, _ = await self._run_update(
            deployment_id,
            DeploymentUpdate(
                spec=BaseDeploymentDataUpdate(
                    name=updated_name,
                    description="updated by direct adapter e2e",
                )
            ),
        )
        results.append(
            self._build_result(
                name="live_update_seed_name_description",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_SUCCESS,
            )
        )

        print("[life/5] live_get_after_update_reflects_name")
        status_code, detail, get_after_update = await self._run_get(deployment_id)
        updated_name_ok = bool(get_after_update and getattr(get_after_update, "name", None) == updated_name)
        results.append(
            self._build_result(
                name="live_get_after_update_reflects_name",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_SUCCESS and updated_name_ok,
            )
        )

        print("[life/6] live_get_status_connected")
        status_code, detail, status_result = await self._run_status(deployment_id)
        connected_ok = bool(status_result and getattr(status_result, "provider_data", {}).get("status") == "connected")
        results.append(
            self._build_result(
                name="live_get_status_connected",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_SUCCESS and connected_ok,
            )
        )

        print("[life/7] live_create_execution_success")
        status_code, detail, execution_create_result = await self._run_create_execution(
            deployment_id,
            provider_data={"message": {"role": "user", "content": "hi"}},
        )
        has_execution_id = bool(execution_create_result and getattr(execution_create_result, "execution_id", None))
        create_pr = getattr(execution_create_result, "provider_result", None) or {}
        create_pr_ok = (
            has_execution_id
            and isinstance(create_pr, dict)
            and "execution_id" in create_pr
            and "run_id" not in create_pr
            and create_pr.get("status") is not None
        )
        results.append(
            self._build_result(
                name="live_create_execution_success",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_SUCCESS and create_pr_ok,
            )
        )

        execution_id_value = (
            execution_create_result.execution_id
            if execution_create_result and getattr(execution_create_result, "execution_id", None)
            else None
        )
        execution_id = str(execution_id_value) if execution_id_value else None

        print("[life/7b] live_create_execution_input_string")
        status_code, detail, exec_str_result = await self._run_create_execution(
            deployment_id,
            provider_data={"input": "hi again"},
        )
        str_ok = bool(
            status_code == OUTCOME_SUCCESS and exec_str_result and getattr(exec_str_result, "execution_id", None)
        )
        results.append(
            self._build_result(
                name="live_create_execution_input_string",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=str_ok,
            )
        )

        print("[life/7c] live_create_execution_input_dict_content")
        status_code, detail, exec_dict_result = await self._run_create_execution(
            deployment_id,
            provider_data={"input": {"content": "haha"}},
        )
        dict_ok = bool(
            status_code == OUTCOME_SUCCESS and exec_dict_result and getattr(exec_dict_result, "execution_id", None)
        )
        results.append(
            self._build_result(
                name="live_create_execution_input_dict_content",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=dict_ok,
            )
        )

        if execution_id:
            print("[life/8] live_get_execution_poll_terminal")
            terminal_result = await self._poll_execution_terminal(execution_id)
            poll_status_code = terminal_result[0]
            poll_detail = terminal_result[1]
            poll_result = terminal_result[2]
            poll_pr = getattr(poll_result, "provider_result", None) or {}
            got_terminal = isinstance(poll_pr, dict) and poll_pr.get("status") in EXECUTION_TERMINAL_STATUSES
            pr_has_execution_id = isinstance(poll_pr, dict) and "execution_id" in poll_pr
            pr_no_run_id = isinstance(poll_pr, dict) and "run_id" not in poll_pr
            results.append(
                self._build_result(
                    name="live_get_execution_poll_terminal",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=poll_status_code,
                    detail=poll_detail,
                    ok=poll_status_code == OUTCOME_SUCCESS and got_terminal and pr_has_execution_id and pr_no_run_id,
                )
            )

            print("[life/8b] live_get_execution_terminal_fields")
            terminal_fields_ok = (
                got_terminal
                and isinstance(poll_pr, dict)
                and poll_pr.get("agent_id") is not None
                and (
                    poll_pr.get("completed_at") is not None
                    or poll_pr.get("failed_at") is not None
                    or poll_pr.get("cancelled_at") is not None
                )
            )
            results.append(
                self._build_result(
                    name="live_get_execution_terminal_fields",
                    expected={OUTCOME_SUCCESS},
                    actual_outcome=poll_status_code,
                    detail=f"status={poll_pr.get('status')} has_timestamps={terminal_fields_ok}",
                    ok=poll_status_code == OUTCOME_SUCCESS and terminal_fields_ok,
                )
            )

        print("[life/9] live_delete_seed")
        status_code, detail, _ = await self._run_delete(deployment_id)
        delete_ok = status_code == OUTCOME_SUCCESS
        if delete_ok:
            self.created_deployment_ids.discard(deployment_id)
        results.append(
            self._build_result(
                name="live_delete_seed",
                expected={OUTCOME_SUCCESS},
                actual_outcome=status_code,
                detail=detail,
                ok=delete_ok,
            )
        )

        print("[life/10] live_get_after_delete_not_found")
        status_code, detail, _ = await self._run_get(deployment_id)
        results.append(
            self._build_result(
                name="live_get_after_delete_not_found",
                expected={OUTCOME_NOT_FOUND},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_NOT_FOUND,
            )
        )

        print("[life/11] live_status_after_delete_not_found_state")
        status_code, detail, _ = await self._run_status(deployment_id)
        results.append(
            self._build_result(
                name="live_status_after_delete_not_found_state",
                expected={OUTCOME_NOT_FOUND},
                actual_outcome=status_code,
                detail=detail,
                ok=status_code == OUTCOME_NOT_FOUND,
            )
        )

        return results