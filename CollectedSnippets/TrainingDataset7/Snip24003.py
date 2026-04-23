def get_layer():
            # This DataSource object is not accessible outside this
            # scope. However, a reference should still be kept alive
            # on the `Layer` returned.
            ds = DataSource(source.ds)
            return ds[0]