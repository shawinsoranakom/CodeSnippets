def write_piff_header(stream, params):
    track_id = params['track_id']
    fourcc = params['fourcc']
    duration = params['duration']
    timescale = params.get('timescale', 10000000)
    language = params.get('language', 'und')
    height = params.get('height', 0)
    width = params.get('width', 0)
    is_audio = width == 0 and height == 0
    creation_time = modification_time = int(time.time())

    ftyp_payload = b'isml'  # major brand
    ftyp_payload += u32.pack(1)  # minor version
    ftyp_payload += b'piff' + b'iso2'  # compatible brands
    stream.write(box(b'ftyp', ftyp_payload))  # File Type Box

    mvhd_payload = u64.pack(creation_time)
    mvhd_payload += u64.pack(modification_time)
    mvhd_payload += u32.pack(timescale)
    mvhd_payload += u64.pack(duration)
    mvhd_payload += s1616.pack(1)  # rate
    mvhd_payload += s88.pack(1)  # volume
    mvhd_payload += u16.pack(0)  # reserved
    mvhd_payload += u32.pack(0) * 2  # reserved
    mvhd_payload += unity_matrix
    mvhd_payload += u32.pack(0) * 6  # pre defined
    mvhd_payload += u32.pack(0xffffffff)  # next track id
    moov_payload = full_box(b'mvhd', 1, 0, mvhd_payload)  # Movie Header Box

    tkhd_payload = u64.pack(creation_time)
    tkhd_payload += u64.pack(modification_time)
    tkhd_payload += u32.pack(track_id)  # track id
    tkhd_payload += u32.pack(0)  # reserved
    tkhd_payload += u64.pack(duration)
    tkhd_payload += u32.pack(0) * 2  # reserved
    tkhd_payload += s16.pack(0)  # layer
    tkhd_payload += s16.pack(0)  # alternate group
    tkhd_payload += s88.pack(1 if is_audio else 0)  # volume
    tkhd_payload += u16.pack(0)  # reserved
    tkhd_payload += unity_matrix
    tkhd_payload += u1616.pack(width)
    tkhd_payload += u1616.pack(height)
    trak_payload = full_box(b'tkhd', 1, TRACK_ENABLED | TRACK_IN_MOVIE | TRACK_IN_PREVIEW, tkhd_payload)  # Track Header Box

    mdhd_payload = u64.pack(creation_time)
    mdhd_payload += u64.pack(modification_time)
    mdhd_payload += u32.pack(timescale)
    mdhd_payload += u64.pack(duration)
    mdhd_payload += u16.pack(((ord(language[0]) - 0x60) << 10) | ((ord(language[1]) - 0x60) << 5) | (ord(language[2]) - 0x60))
    mdhd_payload += u16.pack(0)  # pre defined
    mdia_payload = full_box(b'mdhd', 1, 0, mdhd_payload)  # Media Header Box

    hdlr_payload = u32.pack(0)  # pre defined
    hdlr_payload += b'soun' if is_audio else b'vide'  # handler type
    hdlr_payload += u32.pack(0) * 3  # reserved
    hdlr_payload += (b'Sound' if is_audio else b'Video') + b'Handler\0'  # name
    mdia_payload += full_box(b'hdlr', 0, 0, hdlr_payload)  # Handler Reference Box

    if is_audio:
        smhd_payload = s88.pack(0)  # balance
        smhd_payload += u16.pack(0)  # reserved
        media_header_box = full_box(b'smhd', 0, 0, smhd_payload)  # Sound Media Header
    else:
        vmhd_payload = u16.pack(0)  # graphics mode
        vmhd_payload += u16.pack(0) * 3  # opcolor
        media_header_box = full_box(b'vmhd', 0, 1, vmhd_payload)  # Video Media Header
    minf_payload = media_header_box

    dref_payload = u32.pack(1)  # entry count
    dref_payload += full_box(b'url ', 0, SELF_CONTAINED, b'')  # Data Entry URL Box
    dinf_payload = full_box(b'dref', 0, 0, dref_payload)  # Data Reference Box
    minf_payload += box(b'dinf', dinf_payload)  # Data Information Box

    stsd_payload = u32.pack(1)  # entry count

    sample_entry_payload = u8.pack(0) * 6  # reserved
    sample_entry_payload += u16.pack(1)  # data reference index
    if is_audio:
        sample_entry_payload += u32.pack(0) * 2  # reserved
        sample_entry_payload += u16.pack(params.get('channels', 2))
        sample_entry_payload += u16.pack(params.get('bits_per_sample', 16))
        sample_entry_payload += u16.pack(0)  # pre defined
        sample_entry_payload += u16.pack(0)  # reserved
        sample_entry_payload += u1616.pack(params['sampling_rate'])

        if fourcc == 'AACL':
            sample_entry_box = box(b'mp4a', sample_entry_payload)
    else:
        sample_entry_payload += u16.pack(0)  # pre defined
        sample_entry_payload += u16.pack(0)  # reserved
        sample_entry_payload += u32.pack(0) * 3  # pre defined
        sample_entry_payload += u16.pack(width)
        sample_entry_payload += u16.pack(height)
        sample_entry_payload += u1616.pack(0x48)  # horiz resolution 72 dpi
        sample_entry_payload += u1616.pack(0x48)  # vert resolution 72 dpi
        sample_entry_payload += u32.pack(0)  # reserved
        sample_entry_payload += u16.pack(1)  # frame count
        sample_entry_payload += u8.pack(0) * 32  # compressor name
        sample_entry_payload += u16.pack(0x18)  # depth
        sample_entry_payload += s16.pack(-1)  # pre defined

        codec_private_data = binascii.unhexlify(params['codec_private_data'].encode('utf-8'))
        if fourcc in ('H264', 'AVC1'):
            sps, pps = codec_private_data.split(u32.pack(1))[1:]
            avcc_payload = u8.pack(1)  # configuration version
            avcc_payload += sps[1:4]  # avc profile indication + profile compatibility + avc level indication
            avcc_payload += u8.pack(0xfc | (params.get('nal_unit_length_field', 4) - 1))  # complete representation (1) + reserved (11111) + length size minus one
            avcc_payload += u8.pack(1)  # reserved (0) + number of sps (0000001)
            avcc_payload += u16.pack(len(sps))
            avcc_payload += sps
            avcc_payload += u8.pack(1)  # number of pps
            avcc_payload += u16.pack(len(pps))
            avcc_payload += pps
            sample_entry_payload += box(b'avcC', avcc_payload)  # AVC Decoder Configuration Record
            sample_entry_box = box(b'avc1', sample_entry_payload)  # AVC Simple Entry
    stsd_payload += sample_entry_box

    stbl_payload = full_box(b'stsd', 0, 0, stsd_payload)  # Sample Description Box

    stts_payload = u32.pack(0)  # entry count
    stbl_payload += full_box(b'stts', 0, 0, stts_payload)  # Decoding Time to Sample Box

    stsc_payload = u32.pack(0)  # entry count
    stbl_payload += full_box(b'stsc', 0, 0, stsc_payload)  # Sample To Chunk Box

    stco_payload = u32.pack(0)  # entry count
    stbl_payload += full_box(b'stco', 0, 0, stco_payload)  # Chunk Offset Box

    minf_payload += box(b'stbl', stbl_payload)  # Sample Table Box

    mdia_payload += box(b'minf', minf_payload)  # Media Information Box

    trak_payload += box(b'mdia', mdia_payload)  # Media Box

    moov_payload += box(b'trak', trak_payload)  # Track Box

    mehd_payload = u64.pack(duration)
    mvex_payload = full_box(b'mehd', 1, 0, mehd_payload)  # Movie Extends Header Box

    trex_payload = u32.pack(track_id)  # track id
    trex_payload += u32.pack(1)  # default sample description index
    trex_payload += u32.pack(0)  # default sample duration
    trex_payload += u32.pack(0)  # default sample size
    trex_payload += u32.pack(0)  # default sample flags
    mvex_payload += full_box(b'trex', 0, 0, trex_payload)  # Track Extends Box

    moov_payload += box(b'mvex', mvex_payload)  # Movie Extends Box
    stream.write(box(b'moov', moov_payload))