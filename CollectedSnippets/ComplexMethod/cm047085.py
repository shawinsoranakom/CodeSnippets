def get_response(
        self,
        as_attachment=None,
        immutable=None,
        content_security_policy="default-src 'none'",
        **send_file_kwargs
    ):
        """
        Create the corresponding :class:`~Response` for the current stream.

        :param bool|None as_attachment: Indicate to the browser that it
            should offer to save the file instead of displaying it.
        :param bool|None immutable: Add the ``immutable`` directive to
            the ``Cache-Control`` response header, allowing intermediary
            proxies to aggressively cache the response. This option also
            set the ``max-age`` directive to 1 year.
        :param str|None content_security_policy: Optional value for the
            ``Content-Security-Policy`` (CSP) header. This header is
            used by browsers to allow/restrict the downloaded resource
            to itself perform new http requests. By default CSP is set
            to ``"default-scr 'none'"`` which restrict all requests.
        :param send_file_kwargs: Other keyword arguments to send to
            :func:`odoo.tools._vendor.send_file.send_file` instead of
            the stream sensitive values. Discouraged.
        """
        assert self.type in ('url', 'data', 'path'), "Invalid type: {self.type!r}, should be 'url', 'data' or 'path'."
        assert getattr(self, self.type) is not None, "There is nothing to stream, missing {self.type!r} attribute."

        if self.type == 'url':
            if self.max_age is not None:
                res = request.redirect(self.url, code=302, local=False)
                res.headers['Cache-Control'] = f'max-age={self.max_age}'
                return res
            return request.redirect(self.url, code=301, local=False)

        if as_attachment is None:
            as_attachment = self.as_attachment
        if immutable is None:
            immutable = self.immutable

        send_file_kwargs = {
            'mimetype': self.mimetype,
            'as_attachment': as_attachment,
            'download_name': self.download_name,
            'conditional': self.conditional,
            'etag': self.etag,
            'last_modified': self.last_modified,
            'max_age': STATIC_CACHE_LONG if immutable else self.max_age,
            'environ': request.httprequest.environ,
            'response_class': Response,
            **send_file_kwargs,
        }

        if self.type == 'data':
            res = _send_file(BytesIO(self.data), **send_file_kwargs)
        else:  # self.type == 'path'
            send_file_kwargs['use_x_sendfile'] = False
            if config['x_sendfile']:
                with contextlib.suppress(ValueError):  # outside of the filestore
                    fspath = Path(self.path).relative_to(opj(config['data_dir'], 'filestore'))
                    x_accel_redirect = f'/web/filestore/{fspath}'
                    send_file_kwargs['use_x_sendfile'] = True

            res = _send_file(self.path, **send_file_kwargs)
            if 'X-Sendfile' in res.headers:
                res.headers['X-Accel-Redirect'] = x_accel_redirect

                # In case of X-Sendfile/X-Accel-Redirect, the body is empty,
                # yet werkzeug gives the length of the file. This makes
                # NGINX wait for content that'll never arrive.
                res.headers['Content-Length'] = '0'

        res.headers['X-Content-Type-Options'] = 'nosniff'

        if content_security_policy:  # see also Application.set_csp()
            res.headers['Content-Security-Policy'] = content_security_policy

        if self.public:
            if (res.cache_control.max_age or 0) > 0:
                res.cache_control.public = True
        else:
            res.cache_control.pop('public', '')
            res.cache_control.private = True
        if immutable:
            res.cache_control['immutable'] = None  # None sets the directive

        return res