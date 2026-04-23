async def test_design(context):
    # Mock new design env
    prd = "我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"
    context.kwargs.project_path = context.config.project_path
    context.kwargs.inc = False
    filename = "prd.txt"
    repo = ProjectRepo(context.kwargs.project_path)
    await repo.docs.prd.save(filename=filename, content=prd)
    kvs = {
        "project_path": str(context.kwargs.project_path),
        "changed_prd_filenames": [str(repo.docs.prd.workdir / filename)],
    }
    instruct_content = AIMessage.create_instruct_value(kvs=kvs, class_name="WritePRDOutput")

    design_api = WriteDesign(context=context)
    result = await design_api.run([Message(content=prd, instruct_content=instruct_content)])
    logger.info(result)
    assert result
    assert isinstance(result, AIMessage)
    assert result.instruct_content
    assert repo.docs.system_design.changed_files

    # Mock incremental design env
    context.kwargs.inc = True
    await repo.docs.prd.save(filename=filename, content=str(REFINED_PRD_JSON))
    await repo.docs.system_design.save(filename=filename, content=DESIGN_SAMPLE)

    result = await design_api.run([Message(content="", instruct_content=instruct_content)])
    logger.info(result)
    assert result
    assert isinstance(result, AIMessage)
    assert result.instruct_content
    assert repo.docs.system_design.changed_files