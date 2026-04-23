def run(self, info):
        metadata = {}

        def add(meta_list, info_list=None):
            if not info_list:
                info_list = meta_list
            if not isinstance(meta_list, (list, tuple)):
                meta_list = (meta_list,)
            if not isinstance(info_list, (list, tuple)):
                info_list = (info_list,)
            for info_f in info_list:
                if info.get(info_f) is not None:
                    for meta_f in meta_list:
                        metadata[meta_f] = info[info_f]
                    break

        # See [1-4] for some info on media metadata/metadata supported
        # by ffmpeg.
        # 1. https://kdenlive.org/en/project/adding-meta-data-to-mp4-video/
        # 2. https://wiki.multimedia.cx/index.php/FFmpeg_Metadata
        # 3. https://kodi.wiki/view/Video_file_tagging
        # 4. http://atomicparsley.sourceforge.net/mpeg-4files.html

        add('title', ('track', 'title'))
        add('date', 'upload_date')
        add(('description', 'comment'), 'description')
        add('purl', 'webpage_url')
        add('track', 'track_number')
        add('artist', ('artist', 'creator', 'uploader', 'uploader_id'))
        add('genre')
        add('album')
        add('album_artist')
        add('disc', 'disc_number')
        add('show', 'series')
        add('season_number')
        add('episode_id', ('episode', 'episode_id'))
        add('episode_sort', 'episode_number')

        if not metadata:
            self._downloader.to_screen('[ffmpeg] There isn\'t any metadata to add')
            return [], info

        filename = info['filepath']
        temp_filename = prepend_extension(filename, 'temp')
        in_filenames = [filename]
        options = []

        if info['ext'] == 'm4a':
            options.extend(['-vn', '-acodec', 'copy'])
        else:
            options.extend(['-c', 'copy'])

        for (name, value) in metadata.items():
            options.extend(['-metadata', '%s=%s' % (name, value)])

        chapters = info.get('chapters', [])
        if chapters:
            metadata_filename = replace_extension(filename, 'meta')
            with open(metadata_filename, 'w', encoding='utf-8') as f:
                def ffmpeg_escape(text):
                    return re.sub(r'(=|;|#|\\|\n)', r'\\\1', text)

                metadata_file_content = ';FFMETADATA1\n'
                for chapter in chapters:
                    metadata_file_content += '[CHAPTER]\nTIMEBASE=1/1000\n'
                    metadata_file_content += 'START=%d\n' % (chapter['start_time'] * 1000)
                    metadata_file_content += 'END=%d\n' % (chapter['end_time'] * 1000)
                    chapter_title = chapter.get('title')
                    if chapter_title:
                        metadata_file_content += 'title=%s\n' % ffmpeg_escape(chapter_title)
                f.write(metadata_file_content)
                in_filenames.append(metadata_filename)
                options.extend(['-map_metadata', '1'])

        self._downloader.to_screen('[ffmpeg] Adding metadata to \'%s\'' % filename)
        self.run_ffmpeg_multiple_files(in_filenames, temp_filename, options)
        if chapters:
            os.remove(metadata_filename)
        os.remove(encodeFilename(filename))
        os.rename(encodeFilename(temp_filename), encodeFilename(filename))
        return [], info