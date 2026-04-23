def run(self, info):
        self._fixup_chapters(info)
        filename, metadata_filename = info['filepath'], None
        files_to_delete, options = [], []
        if self._add_chapters and info.get('chapters'):
            metadata_filename = replace_extension(filename, 'meta')
            options.extend(self._get_chapter_opts(info['chapters'], metadata_filename))
            files_to_delete.append(metadata_filename)
        if self._add_metadata:
            options.extend(self._get_metadata_opts(info))

        if self._add_infojson:
            if info['ext'] in ('mkv', 'mka'):
                infojson_filename = info.get('infojson_filename')
                options.extend(self._get_infojson_opts(info, infojson_filename))
                if not infojson_filename:
                    files_to_delete.append(info.get('infojson_filename'))
            elif self._add_infojson is True:
                self.to_screen('The info-json can only be attached to mkv/mka files')

        if not options:
            self.to_screen('There isn\'t any metadata to add')
            return [], info

        temp_filename = prepend_extension(filename, 'temp')
        self.to_screen(f'Adding metadata to "{filename}"')
        self.run_ffmpeg_multiple_files(
            (filename, metadata_filename), temp_filename,
            itertools.chain(self._options(info['ext']), *options))
        self._delete_downloaded_files(*files_to_delete)
        os.replace(temp_filename, filename)
        return [], info