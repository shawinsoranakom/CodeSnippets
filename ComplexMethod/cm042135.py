async def test_write_prd(new_filename, context):
    product_manager = ProductManager(context=context)
    requirements = "开发一个基于大语言模型与私有知识库的搜索引擎，希望可以基于大语言模型进行搜索总结"
    product_manager.rc.react_mode = RoleReactMode.BY_ORDER
    prd = await product_manager.run(Message(content=requirements, cause_by=UserRequirement))
    assert prd.cause_by == any_to_str(WritePRD)
    logger.info(requirements)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    repo = ProjectRepo(context.kwargs.project_path)
    assert repo.docs.prd.changed_files
    repo.git_repo.archive()

    # Mock incremental requirement
    context.config.inc = True
    context.config.project_path = context.kwargs.project_path
    repo = ProjectRepo(context.config.project_path)
    await repo.docs.save(filename=REQUIREMENT_FILENAME, content=NEW_REQUIREMENT_SAMPLE)

    action = WritePRD(context=context)
    prd = await action.run([Message(content=NEW_REQUIREMENT_SAMPLE, instruct_content=None)])
    logger.info(NEW_REQUIREMENT_SAMPLE)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    assert repo.git_repo.changed_files