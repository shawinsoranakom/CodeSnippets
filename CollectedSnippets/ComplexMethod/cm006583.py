def test_generic_parametrization_applies_to_result_and_list_models() -> None:
    typed_create = DeploymentCreateResult[_ResultModel](
        id="dep_1",
        provider_result={"external_url": "https://dep.example"},
    )
    typed_operation = DeploymentOperationResult[_ResultModel](
        id="dep_1",
        provider_result={"external_url": "https://dep.example"},
    )
    typed_update = DeploymentUpdateResult[_ResultModel](
        id="dep_1",
        provider_result={"external_url": "https://dep.example"},
    )
    typed_execution = ExecutionResultBase[_ExecutionResultModel](
        execution_id="exec_1",
        deployment_id="dep_1",
        provider_result={"status": "running"},
    )
    typed_execution_create = ExecutionCreateResult[_ExecutionResultModel](
        execution_id="exec_1",
        deployment_id="dep_1",
        provider_result={"status": "running"},
    )
    typed_execution_status = ExecutionStatusResult[_ExecutionResultModel](
        execution_id="exec_1",
        deployment_id="dep_1",
        provider_result={"status": "running"},
    )
    typed_item = ItemResult[_StatusModel](
        id="dep_1",
        name="dep",
        type=DeploymentType.AGENT,
        provider_data={"healthy": True},
    )
    typed_deployment_list = DeploymentListResult[_ResultModel](
        deployments=[],
        provider_result={"external_url": "https://dep.example"},
    )
    typed_config_list = ConfigListResult[_ResultModel](
        configs=[],
        provider_result={"external_url": "https://dep.example"},
    )
    typed_snapshot_list = SnapshotListResult[_ResultModel, _StatusModel](
        snapshots=[],
        provider_result={"external_url": "https://dep.example"},
    )
    typed_config_params = ConfigListParams[_ConfigFilterModel](provider_params={"namespace": "prod"})
    typed_snapshot_params = SnapshotListParams[_SnapshotFilterModel](provider_params={"label": "nightly"})

    assert isinstance(typed_create.provider_result, _ResultModel)
    assert isinstance(typed_operation.provider_result, _ResultModel)
    assert isinstance(typed_update.provider_result, _ResultModel)
    assert isinstance(typed_execution.provider_result, _ExecutionResultModel)
    assert isinstance(typed_execution_create.provider_result, _ExecutionResultModel)
    assert isinstance(typed_execution_status.provider_result, _ExecutionResultModel)
    assert isinstance(typed_item.provider_data, _StatusModel)
    assert isinstance(typed_deployment_list.provider_result, _ResultModel)
    assert isinstance(typed_config_list.provider_result, _ResultModel)
    assert isinstance(typed_snapshot_list.provider_result, _ResultModel)
    assert isinstance(typed_config_params.provider_params, _ConfigFilterModel)
    assert isinstance(typed_snapshot_params.provider_params, _SnapshotFilterModel)