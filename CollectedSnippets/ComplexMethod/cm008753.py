def run(self, info):
        entries = info.get('entries') or []
        if not any(entries) or (self._only_multi_video and info['_type'] != 'multi_video'):
            return [], info
        elif traverse_obj(entries, (..., lambda k, v: k == 'requested_downloads' and len(v) > 1)):
            raise PostProcessingError('Concatenation is not supported when downloading multiple separate formats')

        in_files = traverse_obj(entries, (..., 'requested_downloads', 0, 'filepath')) or []
        if len(in_files) < len(entries):
            raise PostProcessingError('Aborting concatenation because some downloads failed')

        exts = traverse_obj(entries, (..., 'requested_downloads', 0, 'ext'), (..., 'ext'))
        ie_copy = collections.ChainMap({'ext': exts[0] if len(set(exts)) == 1 else 'mkv'},
                                       info, self._downloader._playlist_infodict(info))
        out_file = self._downloader.prepare_filename(ie_copy, 'pl_video')

        files_to_delete = self.concat_files(in_files, out_file)

        info['requested_downloads'] = [{
            'filepath': out_file,
            'ext': ie_copy['ext'],
        }]
        return files_to_delete, info