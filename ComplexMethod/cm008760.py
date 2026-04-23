def duration_filter(s):
            start_end = s['segment']
            # Ignore entire video segments (https://wiki.sponsor.ajay.app/w/Types).
            if start_end == (0, 0):
                return False
            # Ignore milliseconds difference at the start.
            if start_end[0] <= 1:
                start_end[0] = 0
            # Make POI chapters 1 sec so that we can properly mark them
            if s['category'] in self.POI_CATEGORIES:
                start_end[1] += 1
            # Ignore milliseconds difference at the end.
            # Never allow the segment to exceed the video.
            if duration and duration - start_end[1] <= 1:
                start_end[1] = duration
            # SponsorBlock duration may be absent or it may deviate from the real one.
            diff = abs(duration - s['videoDuration']) if s['videoDuration'] else 0
            return diff < 1 or (diff < 5 and diff / (start_end[1] - start_end[0]) < 0.05)