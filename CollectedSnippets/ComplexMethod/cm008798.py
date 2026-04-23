def real_download(self, filename, info_dict):
        fragment_base_url = info_dict.get('fragment_base_url')
        fragments = info_dict['fragments'][:1] if self.params.get(
            'test', False) else info_dict['fragments']
        title = info_dict.get('title', info_dict['format_id'])
        origin = info_dict.get('webpage_url', info_dict['url'])

        ctx = {
            'filename': filename,
            'total_frags': len(fragments),
        }

        self._prepare_and_start_frag_download(ctx, info_dict)

        extra_state = ctx.setdefault('extra_state', {
            'header_written': False,
            'mime_boundary': str(uuid.uuid4()).replace('-', ''),
        })

        frag_boundary = extra_state['mime_boundary']

        if not extra_state['header_written']:
            stub = self._gen_stub(
                fragments=fragments,
                frag_boundary=frag_boundary,
                title=title,
            )

            ctx['dest_stream'].write((
                'MIME-Version: 1.0\r\n'
                'From: <nowhere@yt-dlp.github.io.invalid>\r\n'
                'To: <nowhere@yt-dlp.github.io.invalid>\r\n'
                f'Subject: {self._escape_mime(title)}\r\n'
                'Content-type: multipart/related; '
                f'boundary="{frag_boundary}"; '
                'type="text/html"\r\n'
                f'X.yt-dlp.Origin: {origin}\r\n'
                '\r\n'
                f'--{frag_boundary}\r\n'
                'Content-Type: text/html; charset=utf-8\r\n'
                f'Content-Length: {len(stub)}\r\n'
                '\r\n'
                f'{stub}\r\n').encode())
            extra_state['header_written'] = True

        for i, fragment in enumerate(fragments):
            if (i + 1) <= ctx['fragment_index']:
                continue

            fragment_url = fragment.get('url')
            if not fragment_url:
                assert fragment_base_url
                fragment_url = urljoin(fragment_base_url, fragment['path'])

            success = self._download_fragment(ctx, fragment_url, info_dict)
            if not success:
                continue
            frag_content = self._read_fragment(ctx)

            frag_header = io.BytesIO()
            frag_header.write(
                b'--%b\r\n' % frag_boundary.encode('us-ascii'))
            frag_header.write(
                b'Content-ID: <%b>\r\n' % self._gen_cid(i, fragment, frag_boundary).encode('us-ascii'))
            frag_header.write(
                b'Content-type: %b\r\n' % f'image/{imghdr.what(h=frag_content) or "jpeg"}'.encode())
            frag_header.write(
                b'Content-length: %u\r\n' % len(frag_content))
            frag_header.write(
                b'Content-location: %b\r\n' % fragment_url.encode('us-ascii'))
            frag_header.write(
                b'X.yt-dlp.Duration: %f\r\n' % fragment['duration'])
            frag_header.write(b'\r\n')
            self._append_fragment(
                ctx, frag_header.getvalue() + frag_content + b'\r\n')

        ctx['dest_stream'].write(
            b'--%b--\r\n\r\n' % frag_boundary.encode('us-ascii'))
        return self._finish_frag_download(ctx, info_dict)