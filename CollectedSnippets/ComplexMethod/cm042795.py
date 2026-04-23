def print_info(site_info, title, type, size, **kwargs):
    if json_output:
        json_output_.print_info(
            site_info=site_info, title=title, type=type, size=size
        )
        return
    if type:
        type = type.lower()
    if type in ['3gp']:
        type = 'video/3gpp'
    elif type in ['asf', 'wmv']:
        type = 'video/x-ms-asf'
    elif type in ['flv', 'f4v']:
        type = 'video/x-flv'
    elif type in ['mkv']:
        type = 'video/x-matroska'
    elif type in ['mp3']:
        type = 'audio/mpeg'
    elif type in ['mp4']:
        type = 'video/mp4'
    elif type in ['mov']:
        type = 'video/quicktime'
    elif type in ['ts']:
        type = 'video/MP2T'
    elif type in ['webm']:
        type = 'video/webm'

    elif type in ['jpg']:
        type = 'image/jpeg'
    elif type in ['png']:
        type = 'image/png'
    elif type in ['gif']:
        type = 'image/gif'

    if type in ['video/3gpp']:
        type_info = '3GPP multimedia file (%s)' % type
    elif type in ['video/x-flv', 'video/f4v']:
        type_info = 'Flash video (%s)' % type
    elif type in ['video/mp4', 'video/x-m4v']:
        type_info = 'MPEG-4 video (%s)' % type
    elif type in ['video/MP2T']:
        type_info = 'MPEG-2 transport stream (%s)' % type
    elif type in ['video/webm']:
        type_info = 'WebM video (%s)' % type
    # elif type in ['video/ogg']:
    #    type_info = 'Ogg video (%s)' % type
    elif type in ['video/quicktime']:
        type_info = 'QuickTime video (%s)' % type
    elif type in ['video/x-matroska']:
        type_info = 'Matroska video (%s)' % type
    # elif type in ['video/x-ms-wmv']:
    #    type_info = 'Windows Media video (%s)' % type
    elif type in ['video/x-ms-asf']:
        type_info = 'Advanced Systems Format (%s)' % type
    # elif type in ['video/mpeg']:
    #    type_info = 'MPEG video (%s)' % type
    elif type in ['audio/mp4', 'audio/m4a']:
        type_info = 'MPEG-4 audio (%s)' % type
    elif type in ['audio/mpeg']:
        type_info = 'MP3 (%s)' % type
    elif type in ['audio/wav', 'audio/wave', 'audio/x-wav']:
        type_info = 'Waveform Audio File Format ({})'.format(type)

    elif type in ['image/jpeg']:
        type_info = 'JPEG Image (%s)' % type
    elif type in ['image/png']:
        type_info = 'Portable Network Graphics (%s)' % type
    elif type in ['image/gif']:
        type_info = 'Graphics Interchange Format (%s)' % type
    elif type in ['m3u8']:
        if 'm3u8_type' in kwargs:
            if kwargs['m3u8_type'] == 'master':
                type_info = 'M3U8 Master {}'.format(type)
        else:
            type_info = 'M3U8 Playlist {}'.format(type)
    else:
        type_info = 'Unknown type (%s)' % type

    maybe_print('Site:      ', site_info)
    maybe_print('Title:     ', unescape_html(tr(title)))
    print('Type:      ', type_info)
    if type != 'm3u8':
        print(
            'Size:      ', round(size / 1048576, 2),
            'MiB (' + str(size) + ' Bytes)'
        )
    if type == 'm3u8' and 'm3u8_url' in kwargs:
        print('M3U8 Url:   {}'.format(kwargs['m3u8_url']))
    print()