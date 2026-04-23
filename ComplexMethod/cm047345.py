def _run_wkhtmltopdf(
            self,
            bodies,
            report_ref=False,
            header=None,
            footer=None,
            landscape=False,
            specific_paperformat_args=None,
            set_viewport_size=False):
        '''Execute wkhtmltopdf as a subprocess in order to convert html given in input into a pdf
        document.

        :param Iterable[str] bodies: The html bodies of the report, one per page.
        :param report_ref: report reference that is needed to get report paperformat.
        :param str header: The html header of the report containing all headers.
        :param str footer: The html footer of the report containing all footers.
        :param landscape: Force the pdf to be rendered under a landscape format.
        :param specific_paperformat_args: dict of prioritized paperformat arguments.
        :param set_viewport_size: Enable a viewport sized '1024x1280' or '1280x1024' depending of landscape arg.
        :return: Content of the pdf as bytes
        :rtype: bytes
        '''
        paperformat_id = self._get_report(report_ref).get_paperformat() if report_ref else self.get_paperformat()

        # Build the base command args for wkhtmltopdf bin
        command_args = self._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size)

        files_command_args = []

        def delete_file(file_path):
            try:
                os.unlink(file_path)
            except OSError:
                _logger.error('Error when trying to remove file %s', file_path)

        with ExitStack() as stack:

            # Passing the cookie to wkhtmltopdf in order to resolve internal links.
            if request and request.db:
                # Create a temporary session which will not create device logs
                temp_session = root.session_store.new()
                temp_session.update({
                    **request.session,
                    'debug': '',
                    '_trace_disable': True,
                })
                if temp_session.uid:
                    temp_session.session_token = security.compute_session_token(temp_session, self.env)
                root.session_store.save(temp_session)
                stack.callback(root.session_store.delete, temp_session)

                base_url = self._get_report_url()
                domain = urlparse(base_url).hostname
                cookie = f'session_id={temp_session.sid}; HttpOnly; domain={domain}; path=/;'
                cookie_jar_file_fd, cookie_jar_file_path = tempfile.mkstemp(suffix='.txt', prefix='report.cookie_jar.tmp.')
                stack.callback(delete_file, cookie_jar_file_path)
                with closing(os.fdopen(cookie_jar_file_fd, 'wb')) as cookie_jar_file:
                    cookie_jar_file.write(cookie.encode())
                command_args.extend(['--cookie-jar', cookie_jar_file_path])

            if header:
                head_file_fd, head_file_path = tempfile.mkstemp(suffix='.html', prefix='report.header.tmp.')
                stack.callback(delete_file, head_file_path)
                with closing(os.fdopen(head_file_fd, 'wb')) as head_file:
                    head_file.write(header.encode())
                files_command_args.extend(['--header-html', head_file_path])
            if footer:
                foot_file_fd, foot_file_path = tempfile.mkstemp(suffix='.html', prefix='report.footer.tmp.')
                stack.callback(delete_file, foot_file_path)
                with closing(os.fdopen(foot_file_fd, 'wb')) as foot_file:
                    foot_file.write(footer.encode())
                files_command_args.extend(['--footer-html', foot_file_path])

            paths = []
            body_idx = 0
            for body_idx, body in enumerate(bodies):
                prefix = f'report.body.tmp.{body_idx}.'
                body_file_fd, body_file_path = tempfile.mkstemp(suffix='.html', prefix=prefix)
                stack.callback(delete_file, body_file_path)
                with closing(os.fdopen(body_file_fd, 'wb')) as body_file:
                    # HACK: wkhtmltopdf doesn't like big table at all and the
                    #       processing time become exponential with the number
                    #       of rows (like 1H for 250k rows).
                    #
                    #       So we split the table into multiple tables containing
                    #       500 rows each. This reduce the processing time to 1min
                    #       for 250k rows. The number 500 was taken from opw-1689673
                    if len(body) < 4 * 1024 * 1024:  # 4Mib
                        body_file.write(body.encode())
                    else:
                        tree = lxml.html.fromstring(body)
                        _split_table(tree, 500)
                        body_file.write(lxml.html.tostring(tree))
                paths.append(body_file_path)

            pdf_report_fd, pdf_report_path = tempfile.mkstemp(suffix='.pdf', prefix='report.tmp.')
            stack.callback(delete_file, pdf_report_path)
            os.close(pdf_report_fd)

            process = _run_wkhtmltopdf(command_args + files_command_args + paths + [pdf_report_path])
            err = process.stderr

            match process.returncode:
                case 0:
                    pass
                case 1:
                    if body_idx:
                        if not _wkhtml().is_patched_qt:
                            if modules.module.current_test:
                                raise unittest.SkipTest("Unable to convert multiple documents via wkhtmltopdf using unpatched QT")
                            raise UserError(_("Tried to convert multiple documents in wkhtmltopdf using unpatched QT"))

                    _logger.warning("wkhtmltopdf: %s", err)
                case c:
                    message = _(
                        'Wkhtmltopdf failed (error code: %(error_code)s). Memory limit too low or maximum file number of subprocess reached. Message : %(message)s',
                        error_code=c,
                        message=err[-1000:],
                    ) if c == -11 else _(
                        'Wkhtmltopdf failed (error code: %(error_code)s). Message: %(message)s',
                        error_code=c,
                        message=err[-1000:],
                    )
                    _logger.warning(message)
                    raise UserError(message)

            with open(pdf_report_path, 'rb') as pdf_document:
                pdf_content = pdf_document.read()

        return pdf_content