def generate_traceback_frames(*args, **kwargs):
            nonlocal tb_frames
            tb_frames = reporter.get_traceback_frames()