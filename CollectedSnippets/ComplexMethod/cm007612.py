def _yes_playlist(self, playlist_id, video_id, *args, **kwargs):
        # smuggled_data=None, *, playlist_label='playlist', video_label='video'
        smuggled_data = args[0] if len(args) == 1 else kwargs.get('smuggled_data')
        playlist_label = kwargs.get('playlist_label', 'playlist')
        video_label = kwargs.get('video_label', 'video')

        if not playlist_id or not video_id:
            return not video_id

        no_playlist = (smuggled_data or {}).get('force_noplaylist')
        if no_playlist is not None:
            return not no_playlist

        video_id = '' if video_id is True else ' ' + video_id
        noplaylist = self.get_param('noplaylist')
        self.to_screen(
            'Downloading just the {0}{1} because of --no-playlist'.format(video_label, video_id)
            if noplaylist else
            'Downloading {0}{1} - add --no-playlist to download just the {2}{3}'.format(
                playlist_label, '' if playlist_id is True else ' ' + playlist_id,
                video_label, video_id))
        return not noplaylist