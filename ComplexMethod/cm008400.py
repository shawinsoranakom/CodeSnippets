def _yes_playlist(self, playlist_id, video_id, smuggled_data=None, *, playlist_label='playlist', video_label='video'):
        if not playlist_id or not video_id:
            return not video_id

        no_playlist = (smuggled_data or {}).get('force_noplaylist')
        if no_playlist is not None:
            return not no_playlist

        video_id = '' if video_id is True else f' {video_id}'
        playlist_id = '' if playlist_id is True else f' {playlist_id}'
        if self.get_param('noplaylist'):
            self.to_screen(f'Downloading just the {video_label}{video_id} because of --no-playlist')
            return False
        self.to_screen(f'Downloading {playlist_label}{playlist_id} - add --no-playlist to download just the {video_label}{video_id}')
        return True