def test_evaluation_parser_custom_values():
    parser = get_evaluation_parser()
    args = parser.parse_args(
        [
            '-v',
            '-d',
            '/path/to/dir',
            '-t',
            'custom task',
            '-f',
            'task.txt',
            '-c',
            'CustomAgent',
            '-i',
            '50',
            '-b',
            '100.5',
            '--eval-output-dir',
            'custom/output',
            '--eval-n-limit',
            '10',
            '--eval-num-workers',
            '8',
            '--eval-note',
            'Test run',
            '-l',
            'gpt4',
            '-n',
            'test_session',
            '--no-auto-continue',
            '--selected-repo',
            'owner/repo',
        ]
    )

    assert args.directory == '/path/to/dir'
    assert args.task == 'custom task'
    assert args.file == 'task.txt'
    assert args.agent_cls == 'CustomAgent'
    assert args.max_iterations == 50
    assert args.max_budget_per_task == pytest.approx(100.5)
    assert args.eval_output_dir == 'custom/output'
    assert args.eval_n_limit == 10
    assert args.eval_num_workers == 8
    assert args.eval_note == 'Test run'
    assert args.llm_config == 'gpt4'
    assert args.name == 'test_session'
    assert args.no_auto_continue
    assert args.version
    assert args.selected_repo == 'owner/repo'