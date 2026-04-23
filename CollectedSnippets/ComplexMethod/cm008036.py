def _write_thumbnails(self, label, info_dict, filename, thumb_filename_base=None):
        """ Write thumbnails to file and return list of (thumb_filename, final_thumb_filename); or None if error """
        write_all = self.params.get('write_all_thumbnails', False)
        thumbnails, ret = [], []
        if write_all or self.params.get('writethumbnail', False):
            thumbnails = info_dict.get('thumbnails') or []
            if not thumbnails:
                self.to_screen(f'[info] There are no {label} thumbnails to download')
                return ret
        multiple = write_all and len(thumbnails) > 1

        if thumb_filename_base is None:
            thumb_filename_base = filename
        if thumbnails and not thumb_filename_base:
            self.write_debug(f'Skipping writing {label} thumbnail')
            return ret

        if thumbnails and not self._ensure_dir_exists(filename):
            return None

        for idx, t in list(enumerate(thumbnails))[::-1]:
            thumb_ext = t.get('ext') or determine_ext(t['url'], 'jpg')
            if multiple:
                thumb_ext = f'{t["id"]}.{thumb_ext}'
            thumb_display_id = f'{label} thumbnail {t["id"]}'
            thumb_filename = replace_extension(filename, thumb_ext, info_dict.get('ext'))
            thumb_filename_final = replace_extension(thumb_filename_base, thumb_ext, info_dict.get('ext'))

            existing_thumb = self.existing_file((thumb_filename_final, thumb_filename))
            if existing_thumb:
                self.to_screen('[info] {} is already present'.format((
                    thumb_display_id if multiple else f'{label} thumbnail').capitalize()))
                t['filepath'] = existing_thumb
                ret.append((existing_thumb, thumb_filename_final))
            else:
                self.to_screen(f'[info] Downloading {thumb_display_id} ...')
                try:
                    uf = self.urlopen(Request(t['url'], headers=t.get('http_headers', {})))
                    self.to_screen(f'[info] Writing {thumb_display_id} to: {thumb_filename}')
                    with open(thumb_filename, 'wb') as thumbf:
                        shutil.copyfileobj(uf, thumbf)
                    ret.append((thumb_filename, thumb_filename_final))
                    t['filepath'] = thumb_filename
                except network_exceptions as err:
                    if isinstance(err, HTTPError) and err.status == 404:
                        self.to_screen(f'[info] {thumb_display_id.title()} does not exist')
                    else:
                        self.report_warning(f'Unable to download {thumb_display_id}: {err}')
                    thumbnails.pop(idx)
            if ret and not write_all:
                break
        return ret