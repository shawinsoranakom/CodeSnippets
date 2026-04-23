def test_cfn_statemachine_with_dependencies(deploy_cfn_template, aws_client):
    sm_name = f"sm_{short_uid()}"
    activity_name = f"act_{short_uid()}"
    stack = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../../templates/statemachine_machine_with_activity.yml"
        ),
        max_wait=150,
        parameters={"StateMachineName": sm_name, "ActivityName": activity_name},
    )

    rs = aws_client.stepfunctions.list_state_machines()
    statemachines = [sm for sm in rs["stateMachines"] if sm_name in sm["name"]]
    assert len(statemachines) == 1

    rs = aws_client.stepfunctions.list_activities()
    activities = [act for act in rs["activities"] if activity_name in act["name"]]
    assert len(activities) == 1

    stack.destroy()

    rs = aws_client.stepfunctions.list_state_machines()
    statemachines = [sm for sm in rs["stateMachines"] if sm_name in sm["name"]]

    assert not statemachines