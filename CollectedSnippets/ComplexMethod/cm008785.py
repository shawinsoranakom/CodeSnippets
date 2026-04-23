def real_download(self, filename, info_dict):
        if 'http_dash_segments_generator' in info_dict['protocol'].split('+'):
            real_downloader = None  # No external FD can support --live-from-start
        else:
            if info_dict.get('is_live'):
                self.report_error('Live DASH videos are not supported')
            real_downloader = get_suitable_downloader(
                info_dict, self.params, None, protocol='dash_frag_urls', to_stdout=(filename == '-'))

        real_start = time.time()

        requested_formats = [{**info_dict, **fmt} for fmt in info_dict.get('requested_formats', [])]
        args = []
        for fmt in requested_formats or [info_dict]:
            # Re-extract if --load-info-json is used and 'fragments' was originally a generator
            # See https://github.com/yt-dlp/yt-dlp/issues/13906
            if isinstance(fmt['fragments'], str):
                raise ReExtractInfo('the stream needs to be re-extracted', expected=True)

            try:
                fragment_count = 1 if self.params.get('test') else len(fmt['fragments'])
            except TypeError:
                fragment_count = None
            ctx = {
                'filename': fmt.get('filepath') or filename,
                'live': 'is_from_start' if fmt.get('is_from_start') else fmt.get('is_live'),
                'total_frags': fragment_count,
            }

            if real_downloader:
                self._prepare_external_frag_download(ctx)
            else:
                self._prepare_and_start_frag_download(ctx, fmt)
            ctx['start'] = real_start

            extra_query = None
            extra_param_to_segment_url = info_dict.get('extra_param_to_segment_url')
            if extra_param_to_segment_url:
                extra_query = urllib.parse.parse_qs(extra_param_to_segment_url)

            fragments_to_download = self._get_fragments(fmt, ctx, extra_query)

            if real_downloader:
                self.to_screen(
                    f'[{self.FD_NAME}] Fragment downloads will be delegated to {real_downloader.get_basename()}')
                info_dict['fragments'] = list(fragments_to_download)
                fd = real_downloader(self.ydl, self.params)
                return fd.real_download(filename, info_dict)

            args.append([ctx, fragments_to_download, fmt])

        return self.download_and_append_fragments_multiple(*args, is_fatal=lambda idx: idx == 0)