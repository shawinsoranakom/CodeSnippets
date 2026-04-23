def spatial_ref_sys(self):
        raise NotImplementedError(
            "subclasses of BaseSpatialOperations must a provide spatial_ref_sys() "
            "method"
        )