def _check_drm_formats(self, tp_formats, video_id):
        has_nondrm, drm_manifest = False, ''
        for f in tp_formats:
            if '_sampleaes/' in (f.get('manifest_url') or ''):
                drm_manifest = drm_manifest or f['manifest_url']
                f['has_drm'] = True
            if not f.get('has_drm') and f.get('manifest_url'):
                has_nondrm = True

        nodrm_manifest = re.sub(r'_sampleaes/(\w+)_fp_', r'/\1_no_', drm_manifest)
        if has_nondrm or nodrm_manifest == drm_manifest:
            return

        tp_formats.extend(self._extract_m3u8_formats(
            nodrm_manifest, video_id, m3u8_id='hls', fatal=False) or [])