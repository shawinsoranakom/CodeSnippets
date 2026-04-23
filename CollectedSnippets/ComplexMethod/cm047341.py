def _wkhtml() -> WkhtmlInfo:
    state = 'install'
    bin_path = 'wkhtmltopdf'
    version = ''
    is_patched_qt = False
    dpi_zoom_ratio = False
    try:
        bin_path = find_in_path('wkhtmltopdf')
        process = subprocess.Popen(
            [bin_path, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError:
        _logger.info('You need Wkhtmltopdf to print a pdf version of the reports.')
    else:
        _logger.info('Will use the Wkhtmltopdf binary at %s', bin_path)
        out, _err = process.communicate()
        version = out.decode('ascii')
        if '(with patched qt)' in version:
            is_patched_qt = True
        match = re.search(r'([0-9.]+)', version)
        if match:
            version = match.group(0)
            if parse_version(version) < parse_version('0.12.0'):
                _logger.info('Upgrade Wkhtmltopdf to (at least) 0.12.0')
                state = 'upgrade'
            else:
                state = 'ok'
            if parse_version(version) >= parse_version('0.12.2'):
                dpi_zoom_ratio = True

            if config['workers'] == 1:
                _logger.info('You need to start Odoo with at least two workers to print a pdf version of the reports.')
                state = 'workers'
        else:
            _logger.info('Wkhtmltopdf seems to be broken.')
            state = 'broken'

    wkhtmltoimage_version = None
    image_bin_path = 'wkhtmltoimage'
    try:
        image_bin_path = find_in_path('wkhtmltoimage')
        process = subprocess.Popen(
            [image_bin_path, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError:
        _logger.info('You need Wkhtmltoimage to generate images from html.')
    else:
        _logger.info('Will use the Wkhtmltoimage binary at %s', image_bin_path)
        out, _err = process.communicate()
        match = re.search(rb'([0-9.]+)', out)
        if match:
            wkhtmltoimage_version = parse_version(match.group(0).decode('ascii'))
            if config['workers'] == 1:
                _logger.info('You need to start Odoo with at least two workers to convert images to html.')
        else:
            _logger.info('Wkhtmltoimage seems to be broken.')

    return WkhtmlInfo(
        state=state,
        dpi_zoom_ratio=dpi_zoom_ratio,
        bin=bin_path,
        version=version,
        is_patched_qt=is_patched_qt,
        wkhtmltoimage_bin=image_bin_path,
        wkhtmltoimage_version=wkhtmltoimage_version,
    )