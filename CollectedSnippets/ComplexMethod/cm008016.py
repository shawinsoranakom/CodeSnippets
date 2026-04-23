def _check_formats(self, formats, warning=True):
        for f in formats:
            working = f.get('__working')
            if working is not None:
                if working:
                    yield f
                continue
            self.to_screen('[info] Testing format {}'.format(f['format_id']))
            path = self.get_output_path('temp')
            if not self._ensure_dir_exists(f'{path}/'):
                continue
            temp_file = tempfile.NamedTemporaryFile(suffix='.tmp', delete=False, dir=path or None)
            temp_file.close()
            # If FragmentFD fails when testing a fragment, it will wrongly set a non-zero return code.
            # Save the actual return code for later. See https://github.com/yt-dlp/yt-dlp/issues/13750
            original_retcode = self._download_retcode
            try:
                success, _ = self.dl(temp_file.name, f, test=True)
            except (DownloadError, OSError, ValueError, *network_exceptions):
                success = False
            finally:
                if os.path.exists(temp_file.name):
                    try:
                        os.remove(temp_file.name)
                    except OSError:
                        self.report_warning(f'Unable to delete temporary file "{temp_file.name}"')
            # Restore the actual return code
            self._download_retcode = original_retcode
            f['__working'] = success
            if success:
                f.pop('__needs_testing', None)
                yield f
            else:
                msg = f'Unable to download format {f["format_id"]}. Skipping...'
                if warning:
                    self.report_warning(msg)
                else:
                    self.to_screen(f'[info] {msg}')