def download_and_append_fragments(
            self, ctx, fragments, info_dict, *, is_fatal=(lambda idx: False),
            pack_func=(lambda content, idx: content), finish_func=None,
            tpe=None, interrupt_trigger=(True, )):

        if not self.params.get('skip_unavailable_fragments', True):
            is_fatal = lambda _: True

        def download_fragment(fragment, ctx):
            if not interrupt_trigger[0]:
                return

            frag_index = ctx['fragment_index'] = fragment['frag_index']
            ctx['last_error'] = None
            headers = HTTPHeaderDict(info_dict.get('http_headers'))
            byte_range = fragment.get('byte_range')
            if byte_range:
                headers['Range'] = 'bytes=%d-%d' % (byte_range['start'], byte_range['end'] - 1)

            # Never skip the first fragment
            fatal = is_fatal(fragment.get('index') or (frag_index - 1))

            def error_callback(err, count, retries):
                if fatal and count > retries:
                    ctx['dest_stream'].close()
                self.report_retry(err, count, retries, frag_index, fatal)
                ctx['last_error'] = err

            for retry in RetryManager(self.params.get('fragment_retries'), error_callback):
                try:
                    ctx['fragment_count'] = fragment.get('fragment_count')
                    if not self._download_fragment(
                            ctx, fragment['url'], info_dict, headers, info_dict.get('request_data')):
                        return
                except (HTTPError, IncompleteRead) as err:
                    retry.error = err
                    continue
                except DownloadError:  # has own retry settings
                    if fatal:
                        raise

        def append_fragment(frag_content, frag_index, ctx):
            if frag_content:
                self._append_fragment(ctx, pack_func(frag_content, frag_index))
            elif not is_fatal(frag_index - 1):
                self.report_skip_fragment(frag_index, 'fragment not found')
            else:
                ctx['dest_stream'].close()
                self.report_error(f'fragment {frag_index} not found, unable to continue')
                return False
            return True

        decrypt_fragment = self.decrypter(info_dict)

        max_workers = math.ceil(
            self.params.get('concurrent_fragment_downloads', 1) / ctx.get('max_progress', 1))
        if max_workers > 1:
            def _download_fragment(fragment):
                ctx_copy = ctx.copy()
                download_fragment(fragment, ctx_copy)
                return fragment, fragment['frag_index'], ctx_copy.get('fragment_filename_sanitized')

            with tpe or concurrent.futures.ThreadPoolExecutor(max_workers) as pool:
                try:
                    for fragment, frag_index, frag_filename in pool.map(_download_fragment, fragments):
                        ctx.update({
                            'fragment_filename_sanitized': frag_filename,
                            'fragment_index': frag_index,
                        })
                        if not append_fragment(decrypt_fragment(fragment, self._read_fragment(ctx)), frag_index, ctx):
                            return False
                except KeyboardInterrupt:
                    self._finish_multiline_status()
                    self.report_error(
                        'Interrupted by user. Waiting for all threads to shutdown...', is_error=False, tb=False)
                    pool.shutdown(wait=False)
                    raise
        else:
            for fragment in fragments:
                if not interrupt_trigger[0]:
                    break
                try:
                    download_fragment(fragment, ctx)
                    result = append_fragment(
                        decrypt_fragment(fragment, self._read_fragment(ctx)), fragment['frag_index'], ctx)
                except KeyboardInterrupt:
                    if info_dict.get('is_live'):
                        break
                    raise
                if not result:
                    return False

        if finish_func is not None:
            ctx['dest_stream'].write(finish_func())
            ctx['dest_stream'].flush()
        return self._finish_frag_download(ctx, info_dict)