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