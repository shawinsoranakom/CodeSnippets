def test_evaluation_parser_default_values():
    parser = get_evaluation_parser()
    args = parser.parse_args([])

    assert args.directory is None
    assert args.task == ''
    assert args.file is None
    assert args.agent_cls is None
    assert args.max_iterations is None
    assert args.max_budget_per_task is None
    assert args.eval_output_dir == 'evaluation/evaluation_outputs/outputs'
    assert args.eval_n_limit is None
    assert args.eval_num_workers == 4
    assert args.eval_note is None
    assert args.llm_config is None
    assert args.name == ''
    assert not args.no_auto_continue
    assert args.selected_repo is None