def splitext(self, the_path):
        """
        Like os.path.splitext, but takes off .tar, too
        """
        base, ext = posixpath.splitext(the_path)
        if base.lower().endswith(".tar"):
            ext = base[-4:] + ext
            base = base[:-4]
        return base, ext