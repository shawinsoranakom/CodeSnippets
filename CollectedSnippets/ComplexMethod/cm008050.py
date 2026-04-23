def fixup():
                    do_fixup = True
                    fixup_policy = self.params.get('fixup')
                    vid = info_dict['id']

                    if fixup_policy in ('ignore', 'never'):
                        return
                    elif fixup_policy == 'warn':
                        do_fixup = 'warn'
                    elif fixup_policy != 'force':
                        assert fixup_policy in ('detect_or_warn', None)
                        if not info_dict.get('__real_download'):
                            do_fixup = False

                    def ffmpeg_fixup(cndn, msg, cls):
                        if not (do_fixup and cndn):
                            return
                        elif do_fixup == 'warn':
                            self.report_warning(f'{vid}: {msg}')
                            return
                        pp = cls(self)
                        if pp.available:
                            info_dict['__postprocessors'].append(pp)
                        else:
                            self.report_warning(f'{vid}: {msg}. Install ffmpeg to fix this automatically')

                    stretched_ratio = info_dict.get('stretched_ratio')
                    ffmpeg_fixup(stretched_ratio not in (1, None),
                                 f'Non-uniform pixel ratio {stretched_ratio}',
                                 FFmpegFixupStretchedPP)

                    downloader = get_suitable_downloader(info_dict, self.params) if 'protocol' in info_dict else None
                    downloader = downloader.FD_NAME if downloader else None

                    ext = info_dict.get('ext')
                    postprocessed_by_ffmpeg = info_dict.get('requested_formats') or any((
                        isinstance(pp, FFmpegVideoConvertorPP)
                        and resolve_recode_mapping(ext, pp.mapping)[0] not in (ext, None)
                    ) for pp in self._pps['post_process'])

                    if not postprocessed_by_ffmpeg:
                        ffmpeg_fixup(fd != FFmpegFD and ext == 'm4a'
                                     and info_dict.get('container') == 'm4a_dash',
                                     'writing DASH m4a. Only some players support this container',
                                     FFmpegFixupM4aPP)
                        ffmpeg_fixup((downloader == 'hlsnative' and not self.params.get('hls_use_mpegts'))
                                     or (info_dict.get('is_live') and self.params.get('hls_use_mpegts') is None),
                                     'Possible MPEG-TS in MP4 container or malformed AAC timestamps',
                                     FFmpegFixupM3u8PP)
                        ffmpeg_fixup(downloader == 'dashsegments'
                                     and (info_dict.get('is_live') or info_dict.get('is_dash_periods')),
                                     'Possible duplicate MOOV atoms', FFmpegFixupDuplicateMoovPP)

                    ffmpeg_fixup(downloader == 'web_socket_fragment', 'Malformed timestamps detected', FFmpegFixupTimestampPP)
                    ffmpeg_fixup(downloader == 'web_socket_fragment', 'Malformed duration detected', FFmpegFixupDurationPP)