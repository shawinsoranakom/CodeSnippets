async def test_new_coding_context(context):
    # Prerequisites
    demo_path = Path(__file__).parent / "../../data/demo_project"
    deps = json.loads(await aread(demo_path / "dependencies.json"))
    dependency = await context.git_repo.get_dependency()
    for k, v in deps.items():
        await dependency.update(k, set(v))
    data = await aread(demo_path / "system_design.json")
    rqno = "20231221155954.json"
    await awrite(context.repo.workdir / SYSTEM_DESIGN_FILE_REPO / rqno, data)
    data = await aread(demo_path / "tasks.json")
    await awrite(context.repo.workdir / TASK_FILE_REPO / rqno, data)

    context.src_workspace = Path(context.repo.workdir) / "game_2048"

    try:
        filename = "game.py"
        engineer = Engineer(context=context)
        ctx_doc = await engineer._new_coding_doc(
            filename=filename,
            dependency=dependency,
        )
        assert ctx_doc
        assert ctx_doc.filename == filename
        assert ctx_doc.content
        ctx = CodingContext.model_validate_json(ctx_doc.content)
        assert ctx.filename == filename
        assert ctx.design_doc
        assert ctx.design_doc.content
        assert ctx.task_doc
        assert ctx.task_doc.content
        assert ctx.code_doc

        context.git_repo.add_change({f"{TASK_FILE_REPO}/{rqno}": ChangeType.UNTRACTED})
        context.git_repo.commit("mock env")
        await context.repo.with_src_path(context.src_workspace).srcs.save(filename=filename, content="content")
        role = Engineer(context=context)
        assert not role.code_todos
        await role._new_code_actions()
        assert role.code_todos
    finally:
        context.git_repo.delete_repository()