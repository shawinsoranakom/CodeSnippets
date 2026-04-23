def real_download(self, filename, info_dict):
        segments = info_dict['fragments'][:1] if self.params.get(
            'test', False) else info_dict['fragments']

        ctx = {
            'filename': filename,
            'total_frags': len(segments),
        }

        self._prepare_and_start_frag_download(ctx, info_dict)

        extra_state = ctx.setdefault('extra_state', {
            'ism_track_written': False,
        })

        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)

        frag_index = 0
        for segment in segments:
            frag_index += 1
            if frag_index <= ctx['fragment_index']:
                continue

            retry_manager = RetryManager(self.params.get('fragment_retries'), self.report_retry,
                                         frag_index=frag_index, fatal=not skip_unavailable_fragments)
            for retry in retry_manager:
                try:
                    success = self._download_fragment(ctx, segment['url'], info_dict)
                    if not success:
                        return False
                    frag_content = self._read_fragment(ctx)

                    if not extra_state['ism_track_written']:
                        tfhd_data = extract_box_data(frag_content, [b'moof', b'traf', b'tfhd'])
                        info_dict['_download_params']['track_id'] = u32.unpack(tfhd_data[4:8])[0]
                        write_piff_header(ctx['dest_stream'], info_dict['_download_params'])
                        extra_state['ism_track_written'] = True
                    self._append_fragment(ctx, frag_content)
                except HTTPError as err:
                    retry.error = err
                    continue

            if retry_manager.error:
                if not skip_unavailable_fragments:
                    return False
                self.report_skip_fragment(frag_index)

        return self._finish_frag_download(ctx, info_dict)