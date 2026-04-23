def load_xsd_files_from_url(env, url, file_name=None, force_reload=False,
                            request_max_timeout=10, xsd_name_prefix='', xsd_names_filter=None, modify_xsd_content=None):
    """Load XSD file or ZIP archive. Save XSD files as ir.attachment.

    An XSD attachment is saved as {xsd_name_prefix}.{filename} where the filename is either the filename obtained
    from the URL or from the ZIP archive, or the `file_name` param if it is specified and a single XSD is being downloaded.
    A typical prefix is the calling module's name.

    For ZIP archives, XSD files inside it will be saved as attachments, depending on the provided list of XSD names.
    ZIP archive themselves are not saved.

    The XSD files content can be modified by providing the `modify_xsd_content` function as argument.
    Typically, this is used when XSD files depend on each other (with the schemaLocation attribute),
    but it can be used for any purpose.

    :param odoo.api.Environment env: environment of calling module
    :param str url: URL of XSD file/ZIP archive
    :param str file_name: used as attachment name if the URL leads to a single XSD, otherwise ignored
    :param bool force_reload: Deprecated.
    :param int request_max_timeout: maximum time (in seconds) before the request times out
    :param str xsd_name_prefix: if provided, will be added as a prefix to every XSD file name
    :param list | str xsd_names_filter: if provided, will only save the XSD files with these names
    :param func modify_xsd_content: function that takes the xsd content as argument and returns a modified version of it
    :rtype: odoo.api.ir.attachment | bool
    :return: every XSD attachment created/fetched or False if an error occurred (see warning logs)
    """
    import requests  # noqa: PLC0415
    try:
        _logger.info("Fetching file/archive from given URL: %s", url)
        response = requests.get(url, timeout=request_max_timeout)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        _logger.warning('HTTP error: %s with the given URL: %s', error, url)
        return False
    except requests.exceptions.ConnectionError as error:
        _logger.warning('Connection error: %s with the given URL: %s', error, url)
        return False
    except requests.exceptions.Timeout as error:
        _logger.warning('Request timeout: %s with the given URL: %s', error, url)
        return False

    content = response.content
    if not content:
        _logger.warning("The HTTP response from %s is empty (no content)", url)
        return False

    archive = None
    with contextlib.suppress(zipfile.BadZipFile):
        archive = zipfile.ZipFile(BytesIO(content))

    if archive is None:
        if modify_xsd_content:
            content = modify_xsd_content(content)
        if not file_name:
            file_name = f"{url.split('/')[-1]}"
            _logger.info("XSD name not provided, defaulting to %s", file_name)

        prefixed_xsd_name = f"{xsd_name_prefix}.{file_name}" if xsd_name_prefix else file_name
        fetched_attachment = env['ir.attachment'].search([('name', '=', prefixed_xsd_name)], limit=1)
        if fetched_attachment:
            _logger.info("Updating the content of ir.attachment with name: %s", prefixed_xsd_name)
            fetched_attachment.raw = content
            return fetched_attachment
        else:
            _logger.info("Saving XSD file as ir.attachment, with name: %s", prefixed_xsd_name)
            return env['ir.attachment'].create({
                'name': prefixed_xsd_name,
                'raw': content,
                'public': True,
            })

    saved_attachments = env['ir.attachment']
    for file_path in archive.namelist():
        if not file_path.endswith('.xsd'):
            continue

        file_name = file_path.rsplit('/', 1)[-1]

        if xsd_names_filter and file_name not in xsd_names_filter:
            _logger.info("Skipping file with name %s in ZIP archive", file_name)
            continue

        try:
            content = archive.read(file_path)
        except KeyError:
            _logger.warning("Failed to retrieve XSD file with name %s from ZIP archive", file_name)
            continue
        if modify_xsd_content:
            content = modify_xsd_content(content)

        prefixed_xsd_name = f"{xsd_name_prefix}.{file_name}" if xsd_name_prefix else file_name
        fetched_attachment = env['ir.attachment'].search([('name', '=', prefixed_xsd_name)], limit=1)
        if fetched_attachment:
            _logger.info("Updating the content of ir.attachment with name: %s", prefixed_xsd_name)
            fetched_attachment.raw = content
            saved_attachments |= fetched_attachment

        else:
            _logger.info("Saving XSD file as ir.attachment, with name: %s", prefixed_xsd_name)
            saved_attachments |= env['ir.attachment'].create({
                'name': prefixed_xsd_name,
                'raw': content,
                'public': True,
            })

    return saved_attachments