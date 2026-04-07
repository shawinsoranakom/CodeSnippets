def srid(self):
        return bool(wkb_writer_get_include_srid(self.ptr))