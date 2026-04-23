def _write_thumbnails(self, info_dict, filename):
        if self.params.get('writethumbnail', False):
            thumbnails = info_dict.get('thumbnails')
            if thumbnails:
                thumbnails = [thumbnails[-1]]
        elif self.params.get('write_all_thumbnails', False):
            thumbnails = info_dict.get('thumbnails')
        else:
            return

        if not thumbnails:
            # No thumbnails present, so return immediately
            return

        for t in thumbnails:
            thumb_ext = determine_ext(t['url'], 'jpg')
            suffix = '_%s' % t['id'] if len(thumbnails) > 1 else ''
            thumb_display_id = '%s ' % t['id'] if len(thumbnails) > 1 else ''
            t['filename'] = thumb_filename = replace_extension(filename + suffix, thumb_ext, info_dict.get('ext'))

            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(thumb_filename)):
                self.to_screen('[%s] %s: Thumbnail %sis already present' %
                               (info_dict['extractor'], info_dict['id'], thumb_display_id))
            else:
                self.to_screen('[%s] %s: Downloading thumbnail %s...' %
                               (info_dict['extractor'], info_dict['id'], thumb_display_id))
                try:
                    uf = self.urlopen(t['url'])
                    with open(encodeFilename(thumb_filename), 'wb') as thumbf:
                        shutil.copyfileobj(uf, thumbf)
                    self.to_screen('[%s] %s: Writing thumbnail %sto: %s' %
                                   (info_dict['extractor'], info_dict['id'], thumb_display_id, thumb_filename))
                except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                    self.report_warning('Unable to download thumbnail "%s": %s' %
                                        (t['url'], error_to_compat_str(err)))