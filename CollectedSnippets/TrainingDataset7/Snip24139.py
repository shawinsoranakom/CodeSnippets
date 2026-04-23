def _load_interstate_data(self):
        # Interstate (2D / 3D and Geographic/Projected variants)
        for name, line, exp_z in interstate_data:
            line_3d = GEOSGeometry(line, srid=4269)
            line_2d = LineString([coord[:2] for coord in line_3d.coords], srid=4269)

            # Creating a geographic and projected version of the
            # interstate in both 2D and 3D.
            Interstate3D.objects.create(name=name, line=line_3d)
            InterstateProj3D.objects.create(name=name, line=line_3d)
            Interstate2D.objects.create(name=name, line=line_2d)
            InterstateProj2D.objects.create(name=name, line=line_2d)