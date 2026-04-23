def get_traceback_frames(self):
        frames = super().get_traceback_frames()
        return [
            frame
            for frame in frames
            if not isinstance(dict(frame["vars"]).get("self"), Client)
        ]