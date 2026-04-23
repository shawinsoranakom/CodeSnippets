def run(self, info):
        self._fixup_chapters(info)
        # Chapters must be preserved intact when downloading multiple formats of the same video.
        chapters, sponsor_chapters = self._mark_chapters_to_remove(
            copy.deepcopy(info.get('chapters')) or [],
            copy.deepcopy(info.get('sponsorblock_chapters')) or [])
        if not chapters and not sponsor_chapters:
            return [], info

        real_duration = self._get_real_video_duration(info['filepath'])
        if not chapters:
            chapters = [{'start_time': 0, 'end_time': info.get('duration') or real_duration, 'title': info['title']}]

        info['chapters'], cuts = self._remove_marked_arrange_sponsors(chapters + sponsor_chapters)
        if not cuts:
            return [], info
        elif not info['chapters']:
            self.report_warning('You have requested to remove the entire video, which is not possible')
            return [], info

        original_duration, info['duration'] = info.get('duration'), info['chapters'][-1]['end_time']
        if self._duration_mismatch(real_duration, original_duration, 1):
            if not self._duration_mismatch(real_duration, info['duration']):
                self.to_screen(f'Skipping {self.pp_key()} since the video appears to be already cut')
                return [], info
            if not info.get('__real_download'):
                raise PostProcessingError('Cannot cut video since the real and expected durations mismatch. '
                                          'Different chapters may have already been removed')
            else:
                self.write_debug('Expected and actual durations mismatch')

        concat_opts = self._make_concat_opts(cuts, real_duration)
        self.write_debug('Concat spec = {}'.format(', '.join(f'{c.get("inpoint", 0.0)}-{c.get("outpoint", "inf")}' for c in concat_opts)))

        def remove_chapters(file, is_sub):
            return file, self.remove_chapters(file, cuts, concat_opts, self._force_keyframes and not is_sub)

        in_out_files = [remove_chapters(info['filepath'], False)]
        in_out_files.extend(remove_chapters(in_file, True) for in_file in self._get_supported_subs(info))

        # Renaming should only happen after all files are processed
        files_to_remove = []
        for in_file, out_file in in_out_files:
            mtime = os.stat(in_file).st_mtime
            uncut_file = prepend_extension(in_file, 'uncut')
            os.replace(in_file, uncut_file)
            os.replace(out_file, in_file)
            self.try_utime(in_file, mtime, mtime)
            files_to_remove.append(uncut_file)

        return files_to_remove, info