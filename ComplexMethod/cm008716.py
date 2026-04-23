def mpd_feed(itag, client_name, delay):
            """
            @returns (manifest_url, manifest_stream_number, is_live) or None
            """
            for retry in self.RetryManager(fatal=False):
                with lock:
                    refetch_manifest(itag, client_name, delay)

                f = next((f for f in formats if f.get('_itag') == itag and f.get('_client') == client_name), None)
                if not f:
                    if not is_live:
                        retry.error = f'{video_id}: Video is no longer live'
                    else:
                        retry.error = f'Cannot find refreshed manifest for format {itag}{bug_reports_message()}'
                    continue

                # Formats from ended premieres will be missing a manifest_url
                # See https://github.com/yt-dlp/yt-dlp/issues/8543
                if not f.get('manifest_url'):
                    break

                return f['manifest_url'], f['manifest_stream_number'], is_live
            return None