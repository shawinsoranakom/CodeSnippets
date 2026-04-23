def get_traceback_frame_variables(self, request, tb_frame):
        return tb_frame.f_locals.items()