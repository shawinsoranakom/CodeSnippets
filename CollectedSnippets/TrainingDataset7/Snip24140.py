def _load_city_data(self):
        for name, pnt_data in city_data:
            City3D.objects.create(
                name=name,
                point=Point(*pnt_data, srid=4326),
                pointg=Point(*pnt_data, srid=4326),
            )