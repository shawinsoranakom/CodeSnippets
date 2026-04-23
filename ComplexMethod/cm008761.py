def run(self, info):
        mtime = os.stat(info['filepath']).st_mtime
        self.to_screen('Writing metadata to file\'s xattrs')
        for xattrname, infoname in self.XATTR_MAPPING.items():
            try:
                value = info.get(infoname)
                if value:
                    if infoname == 'upload_date':
                        value = hyphenate_date(value)
                    elif xattrname == 'com.apple.metadata:kMDItemWhereFroms':
                        # Colon in xattr name throws errors on Windows/NTFS and Linux
                        if sys.platform != 'darwin':
                            continue
                        value = self.APPLE_PLIST_TEMPLATE % value
                    write_xattr(info['filepath'], xattrname, value.encode())

            except XAttrUnavailableError as e:
                raise PostProcessingError(str(e))
            except XAttrMetadataError as e:
                if e.reason == 'NO_SPACE':
                    self.report_warning(
                        'There\'s no disk space left, disk quota exceeded or filesystem xattr limit exceeded. '
                        f'Extended attribute "{xattrname}" was not written.')
                elif e.reason == 'VALUE_TOO_LONG':
                    self.report_warning(f'Unable to write extended attribute "{xattrname}" due to too long values.')
                else:
                    tip = ('You need to use NTFS' if os.name == 'nt'
                           else 'You may have to enable them in your "/etc/fstab"')
                    raise PostProcessingError(f'This filesystem doesn\'t support extended attributes. {tip}')

        self.try_utime(info['filepath'], mtime, mtime)
        return [], info