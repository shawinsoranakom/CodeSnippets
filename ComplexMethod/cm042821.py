def height_to_quality(height, qn):
        if height <= 360 and qn <= 16:
            return 16
        elif height <= 480 and qn <= 32:
            return 32
        elif height <= 720 and qn <= 64:
            return 64
        elif height <= 1080 and qn <= 80:
            return 80
        elif height <= 1080 and qn <= 112:
            return 112
        else:
            return 120