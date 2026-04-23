def extract_source(source_url, source_id=None):
            if source_url in format_urls:
                return
            format_urls.add(source_url)
            ext = determine_ext(source_url)
            if OnceIE.suitable(source_url):
                formats.extend(self._extract_once_formats(source_url))
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    source_url, video_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    source_url, video_id, f4m_id=source_id, fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=source_id, fatal=False))
            else:
                f = {
                    'url': source_url,
                    'format_id': source_id,
                }
                mobj = re.search(r'(\d+)p(\d+)_(\d+)k\.', source_url)
                if mobj:
                    f.update({
                        'height': int(mobj.group(1)),
                        'fps': int(mobj.group(2)),
                        'tbr': int(mobj.group(3)),
                    })
                if source_id == 'mezzanine':
                    f['preference'] = 1
                formats.append(f)