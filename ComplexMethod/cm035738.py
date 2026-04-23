def test_headless_parser_default_values():
    parser = get_headless_parser()
    args = parser.parse_args([])

    assert args.directory is None
    assert args.task == ''
    assert args.file is None
    assert args.agent_cls is None
    assert args.max_iterations is None
    assert args.max_budget_per_task is None
    assert args.llm_config is None
    assert args.name == ''
    assert not args.no_auto_continue
    assert args.selected_repo is None