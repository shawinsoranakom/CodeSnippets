def do_request_(self, request):
        host = request.host
        if not host:
            raise URLError('no host given')

        if request.data is not None:  # POST
            data = request.data
            if isinstance(data, str):
                msg = "POST data should be bytes, an iterable of bytes, " \
                      "or a file object. It cannot be of type str."
                raise TypeError(msg)
            if not request.has_header('Content-type'):
                request.add_unredirected_header(
                    'Content-type',
                    'application/x-www-form-urlencoded')
            if (not request.has_header('Content-length')
                    and not request.has_header('Transfer-encoding')):
                content_length = self._get_content_length(request)
                if content_length is not None:
                    request.add_unredirected_header(
                            'Content-length', str(content_length))
                else:
                    request.add_unredirected_header(
                            'Transfer-encoding', 'chunked')

        sel_host = host
        if request.has_proxy():
            scheme, sel = _splittype(request.selector)
            sel_host, sel_path = _splithost(sel)
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', sel_host)
        for name, value in self.parent.addheaders:
            name = name.capitalize()
            if not request.has_header(name):
                request.add_unredirected_header(name, value)

        return request