def __extract_slides(self, *, stream_id, snum, stream, duration, images):
        slide_base_url = stream['SlideBaseUrl']

        fname_template = stream['SlideImageFileNameTemplate']
        if fname_template != 'slide_{0:D4}.jpg':
            self.report_warning('Unusual slide file name template; report a bug if slide downloading fails')
        fname_template = re.sub(r'\{0:D([0-9]+)\}', r'{0:0\1}', fname_template)

        fragments = []
        for i, slide in enumerate(stream['Slides']):
            if i == 0:
                if slide['Time'] > 0:
                    default_slide = images.get('DefaultSlide')
                    if default_slide is None:
                        default_slide = images.get('DefaultStreamImage')
                    if default_slide is not None:
                        default_slide = default_slide['ImageFilename']
                    if default_slide is not None:
                        fragments.append({
                            'path': default_slide,
                            'duration': slide['Time'] / 1000,
                        })

            next_time = try_call(
                lambda: stream['Slides'][i + 1]['Time'],
                lambda: duration,
                lambda: slide['Time'],
                expected_type=(int, float))

            fragments.append({
                'path': fname_template.format(slide.get('Number', i + 1)),
                'duration': (next_time - slide['Time']) / 1000,
            })

        return {
            'format_id': f'{stream_id}-{snum}.slides',
            'ext': 'mhtml',
            'url': slide_base_url,
            'protocol': 'mhtml',
            'acodec': 'none',
            'vcodec': 'none',
            'format_note': 'Slides',
            'fragments': fragments,
            'fragment_base_url': slide_base_url,
        }