def main(args):
    checkers = [
        Distribution.get(distro)(release)
        for version in args.release
        for (distro, release) in [version.split(':')]
    ]

    stderr.write("Fetch Python versions...\n")
    pyvers = [
        '.'.join(map(str, checker.get_version('python3-defaults')[:2]))
        for checker in checkers
    ]

    uniq = sorted(set(pyvers), key=parse_version)
    platforms = PLATFORM_NAMES if args.check_pypi else PLATFORM_NAMES[:1]
    platform_codes = PLATFORM_CODES if args.check_pypi else PLATFORM_CODES[:1]
    platform_headers = ['']
    python_headers = ['']
    table = [platform_headers, python_headers]
    # requirements headers
    for v in uniq:
        for p in platforms:
            platform_headers.append(p)
            python_headers.append(v)

    # distro headers
    for checker, version in zip(checkers, pyvers):
        platform_headers.append(checker._release[:5])
        python_headers.append(version)

    reqs = parse_requirements((Path.cwd() / __file__).parent.parent / 'requirements.txt')
    if args.filter:
        reqs = {r: o for r, o in reqs.items() if any(f in r for f in args.filter.split(','))}

    for req, options in reqs.items():
        if args.check_pypi:
            pip_infos = PipPackage(req)
        row = [req]
        seps = [' || ']
        byver = {}
        for pyver in uniq:
            # FIXME: when multiple options apply, check which pip uses
            #        (first-matching. best-matching, latest, ...)
            seps[-1] = ' || '
            for platform in platform_codes:
                platform_version = 'none'
                for version, markers in options:
                    if not markers or markers.evaluate({
                        'python_version': pyver,
                        'sys_platform': platform,
                    }):
                        if platform == 'linux':
                            byver[pyver] = version
                        platform_version = version
                        break
                deco = None
                if args.check_pypi:
                    if platform_version == 'none':
                        deco = 'ok'
                    else:
                        has_wheel_for_version, has_any_wheel, has_wheel_in_another_version = pip_infos.has_wheel_for(platform_version, pyver, platform)
                        if has_wheel_for_version:
                            deco = 'ok'
                        elif has_wheel_in_another_version:
                            deco = 'ko'
                        elif has_any_wheel:
                            deco = 'warn'
                    if deco in ("ok", None):
                        if byver.get(pyver, 'none') != platform_version:
                            deco = 'em'
                req_ver = platform_version or 'any'
                row.append((req_ver, deco))
                seps.append(' | ')

        seps[-1] = ' |#| '
        # this requirement doesn't apply, ignore
        if not byver and not args.all:
            continue

        for i, c in enumerate(checkers):
            req_version = byver.get(pyvers[i], 'none') or 'any'
            check_version = '.'.join(map(str, c.get_version(req.lower()) or [])) or None
            if req_version != check_version:
                deco = 'ko'
                if req_version == 'none':
                    deco = 'ok'
                elif req_version == 'any':
                    if check_version is None:
                        deco = 'ok'
                elif check_version is None:
                    deco = 'ko'
                elif parse_version(req_version) >= parse_version(check_version):
                    deco = 'warn'
                row.append((check_version or '</>', deco))
            elif args.all:
                row.append((check_version or '</>', 'ok'))
            else:
                row.append('')
            seps.append(' |#|  ')
        table.append(row)

    seps[-1] = ' '  # remove last column separator

    stderr.write('\n')

    # evaluate width of columns
    sizes = [0] * len(table[0])
    for row in table:
        sizes = [
            max(s, len(cell[0] if isinstance(cell, tuple) else cell))
            for s, cell in zip(sizes, row)
        ]

    output_format = 'ansi'
    if args.format:
        output_format = args.format
        assert output_format in SUPPORTED_FORMATS
    elif args.output:
        output_format = 'txt'
        ext = args.output.split('.')[-1]
        if ext in SUPPORTED_FORMATS:
            output_format = ext

    if output_format == 'json':
        output = json.dumps(table)
    else:
        output = ''
        # format table
        for row in table:
            output += ' '
            for cell, width, sep in zip(row, sizes, seps):
                cell_content = cell
                deco = default
                if isinstance(cell, tuple):
                    cell_content, level = cell
                    if output_format == 'txt' or level is None:
                        deco = default
                    elif level == 'ok':
                        deco = ok
                    elif level == 'em':
                        deco = em
                    elif level == 'warn':
                        deco = warn
                    else:
                        deco = ko
                output += deco(f'{cell_content:<{width}}') + sep
            output += '\n'

    if output_format in ('svg', 'html'):
        if not ansitoimg:
            output_format = 'ansi'
            stderr.write(f'Missing ansitoimg for {output_format} format, switching to ansi')
        else:
            convert = ansitoimg.ansiToSVG
            if output_format == 'html':
                convert = ansitoimg.ansiToHTML
            with tempfile.NamedTemporaryFile() as tmp:
                convert(output, tmp.name, width=(sum(sizes) + sum(len(sep) for sep in seps)), title='requirements-check.py')
                output = tmp.read().decode()
                # remove mac like bullets
                output = output.replace('''<g transform="translate(26,22)">
            <circle cx="0" cy="0" r="7" fill="#ff5f57"/>
            <circle cx="22" cy="0" r="7" fill="#febc2e"/>
            <circle cx="44" cy="0" r="7" fill="#28c840"/>
            </g>''', "")  #

    if args.output:
        with open(args.output, 'w', encoding='utf8') as f:
            f.write(output)
    else:
        stdout.write(output)