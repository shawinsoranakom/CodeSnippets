def srid(self, include):
        wkb_writer_set_include_srid(self.ptr, bool(include))