def real_download(self, filename, info_dict):
        segments = info_dict['fragments'][:1] if self.params.get(
            'test', False) else info_dict['fragments']

        ctx = {
            'filename': filename,
            'total_frags': len(segments),
        }

        self._prepare_and_start_frag_download(ctx)

        fragment_retries = self.params.get('fragment_retries', 0)
        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)

        track_written = False
        frag_index = 0
        for i, segment in enumerate(segments):
            frag_index += 1
            if frag_index <= ctx['fragment_index']:
                continue
            count = 0
            while count <= fragment_retries:
                try:
                    success, frag_content = self._download_fragment(ctx, segment['url'], info_dict)
                    if not success:
                        return False
                    if not track_written:
                        tfhd_data = extract_box_data(frag_content, [b'moof', b'traf', b'tfhd'])
                        info_dict['_download_params']['track_id'] = u32.unpack(tfhd_data[4:8])[0]
                        write_piff_header(ctx['dest_stream'], info_dict['_download_params'])
                        track_written = True
                    self._append_fragment(ctx, frag_content)
                    break
                except compat_urllib_error.HTTPError as err:
                    count += 1
                    if count <= fragment_retries:
                        self.report_retry_fragment(err, frag_index, count, fragment_retries)
            if count > fragment_retries:
                if skip_unavailable_fragments:
                    self.report_skip_fragment(frag_index)
                    continue
                self.report_error('giving up after %s fragment retries' % fragment_retries)
                return False

        self._finish_frag_download(ctx)

        return True