def incidental_report(args):
    """Generate incidental coverage report."""
    ct = CoverageTool()
    git = Git(os.path.abspath(args.source))
    coverage_data = CoverageData(os.path.abspath(args.result))

    result_sha = args.result_sha or coverage_data.result_sha

    try:
        git.show([result_sha, '--'])
    except subprocess.CalledProcessError:
        raise ApplicationError('%s: commit not found: %s\n'
                               'make sure your source repository is up-to-date' % (git.path, result_sha))

    if coverage_data.result != "succeeded":
        check_failed(args, 'results indicate tests did not pass (result: %s)\n'
                           're-run until passing, then download the latest results and re-run the report using those results' % coverage_data.result)

    if not coverage_data.paths:
        raise ApplicationError('no coverage data found\n'
                               'make sure the downloaded results are from a code coverage run on Azure Pipelines')

    # generate a unique subdirectory in the output directory based on the input files being used
    path_hash = hashlib.sha256(b'\n'.join(p.encode() for p in coverage_data.paths)).hexdigest()
    output_path = os.path.abspath(os.path.join(args.output, path_hash))

    data_path = os.path.join(output_path, 'data')
    reports_path = os.path.join(output_path, 'reports')

    for path in [data_path, reports_path]:
        if not os.path.exists(path):
            os.makedirs(path)

    # combine coverage results into a single file
    combined_path = os.path.join(output_path, 'combined.json')
    cached(combined_path, args.use_cache, args.verbose,
           lambda: ct.combine(coverage_data.paths, combined_path))

    with open(combined_path) as combined_file:
        combined = json.load(combined_file)

    if args.plugin_path:
        # reporting on coverage missing from the test target for the specified plugin
        # the report will be on a single target
        cache_path_format = '%s' + '-for-%s' % os.path.splitext(os.path.basename(args.plugin_path))[0]
        target_pattern = '^%s$' % get_target_name_from_plugin_path(args.plugin_path)
        include_path = args.plugin_path
        missing = True
        target_name = get_target_name_from_plugin_path(args.plugin_path)
    else:
        # reporting on coverage exclusive to the matched targets
        # the report can contain multiple targets
        cache_path_format = '%s'
        target_pattern = args.targets
        include_path = None
        missing = False
        target_name = None

    # identify integration test targets to analyze
    target_names = sorted(combined['targets'])
    incidental_target_names = [target for target in target_names if re.search(target_pattern, target)]

    if not incidental_target_names:
        if target_name:
            # if the plugin has no tests we still want to know what coverage is missing
            incidental_target_names = [target_name]
        else:
            raise ApplicationError('no targets to analyze')

    # exclude test support plugins from analysis
    # also exclude six, which for an unknown reason reports bogus coverage lines (indicating coverage of comments)
    exclude_path = '^(test/support/|lib/ansible/module_utils/six/)'

    # process coverage for each target and then generate a report
    # save sources for generating a summary report at the end
    summary = {}
    report_paths = {}

    for target_name in incidental_target_names:
        cache_name = cache_path_format % target_name

        only_target_path = os.path.join(data_path, 'only-%s.json' % cache_name)
        cached(only_target_path, args.use_cache, args.verbose,
               lambda: ct.filter(combined_path, only_target_path, include_targets=[target_name], include_path=include_path, exclude_path=exclude_path))

        without_target_path = os.path.join(data_path, 'without-%s.json' % cache_name)
        cached(without_target_path, args.use_cache, args.verbose,
               lambda: ct.filter(combined_path, without_target_path, exclude_targets=[target_name], include_path=include_path, exclude_path=exclude_path))

        if missing:
            source_target_path = missing_target_path = os.path.join(data_path, 'missing-%s.json' % cache_name)
            cached(missing_target_path, args.use_cache, args.verbose,
                   lambda: ct.missing(without_target_path, only_target_path, missing_target_path, only_gaps=True))
        else:
            source_target_path = exclusive_target_path = os.path.join(data_path, 'exclusive-%s.json' % cache_name)
            cached(exclusive_target_path, args.use_cache, args.verbose,
                   lambda: ct.missing(only_target_path, without_target_path, exclusive_target_path, only_gaps=True))

        source_expanded_target_path = os.path.join(os.path.dirname(source_target_path), 'expanded-%s' % os.path.basename(source_target_path))
        cached(source_expanded_target_path, args.use_cache, args.verbose,
               lambda: ct.expand(source_target_path, source_expanded_target_path))

        summary[target_name] = sources = collect_sources(source_expanded_target_path, git, coverage_data, result_sha)

        txt_report_path = os.path.join(reports_path, '%s.txt' % cache_name)
        cached(txt_report_path, args.use_cache, args.verbose,
               lambda: generate_report(sources, txt_report_path, coverage_data, target_name, missing=missing))

        report_paths[target_name] = txt_report_path

    # provide a summary report of results
    for target_name in incidental_target_names:
        sources = summary[target_name]
        report_path = os.path.relpath(report_paths[target_name])

        print('%s: %d arcs, %d lines, %d files - %s' % (
            target_name,
            sum(len(s.covered_arcs) for s in sources),
            sum(len(s.covered_lines) for s in sources),
            len(sources),
            report_path,
        ))

    if not missing:
        sys.stderr.write('NOTE: This report shows only coverage exclusive to the reported targets. '
                         'As targets are removed, exclusive coverage on the remaining targets will increase.\n')