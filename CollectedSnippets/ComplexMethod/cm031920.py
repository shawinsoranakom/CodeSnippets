def cmd_data(datacmd, **kwargs):
    formats = dict(c_analyzer.FORMATS)
    formats['summary'] = fmt_summary
    filenames = (file
                 for file in _resolve_filenames(None)
                 if file not in _parser.EXCLUDED)
    kwargs['get_file_preprocessor'] = _parser.get_preprocessor(log_err=print)
    if datacmd == 'show':
        types = _analyzer.read_known()
        results = []
        for decl, info in types.items():
            if info is UNKNOWN:
                if decl.kind in (KIND.STRUCT, KIND.UNION):
                    extra = {'unsupported': ['type unknown'] * len(decl.members)}
                else:
                    extra = {'unsupported': ['type unknown']}
                info = (info, extra)
            results.append((decl, info))
            if decl.shortkey == 'struct _object':
                tempinfo = info
        known = _analyzer.Analysis.from_results(results)
        analyze = None
    elif datacmd == 'dump':
        known = _analyzer.KNOWN_FILE
        def analyze(files, **kwargs):
            decls = []
            for decl in _analyzer.iter_decls(files, **kwargs):
                if not KIND.is_type_decl(decl.kind):
                    continue
                if not decl.filename.endswith('.h'):
                    if decl.shortkey not in _analyzer.KNOWN_IN_DOT_C:
                        continue
                decls.append(decl)
            results = _c_analyzer.analyze_decls(
                decls,
                known={},
                analyze_resolved=_analyzer.analyze_resolved,
            )
            return _analyzer.Analysis.from_results(results)
    else:  # check
        known = _analyzer.read_known()
        def analyze(files, **kwargs):
            return _analyzer.iter_decls(files, **kwargs)
    extracolumns = None
    c_analyzer.cmd_data(
        datacmd,
        filenames,
        known,
        _analyze=analyze,
        formats=formats,
        extracolumns=extracolumns,
        relroot=REPO_ROOT,
        **kwargs
    )