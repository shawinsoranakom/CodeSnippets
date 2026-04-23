def test_cli_argparse_record_start_stop():
	"""`browser-use record start <path>` and `record stop` parse correctly."""
	from browser_use.skill_cli.main import build_parser

	parser = build_parser()

	args = parser.parse_args(['record', 'start', '/tmp/x.mp4'])
	assert args.command == 'record'
	assert args.record_command == 'start'
	assert args.path == '/tmp/x.mp4'

	args = parser.parse_args(['record', 'stop'])
	assert args.command == 'record'
	assert args.record_command == 'stop'

	args = parser.parse_args(['record', 'status'])
	assert args.command == 'record'
	assert args.record_command == 'status'