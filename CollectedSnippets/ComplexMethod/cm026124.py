def _convert_supported_features(
        zha_features: ZHACoverEntityFeature,
    ) -> CoverEntityFeature:
        """Convert ZHA cover features to HA cover features."""
        features = CoverEntityFeature(0)

        if ZHACoverEntityFeature.OPEN in zha_features:
            features |= CoverEntityFeature.OPEN
        if ZHACoverEntityFeature.CLOSE in zha_features:
            features |= CoverEntityFeature.CLOSE
        if ZHACoverEntityFeature.SET_POSITION in zha_features:
            features |= CoverEntityFeature.SET_POSITION
        if ZHACoverEntityFeature.STOP in zha_features:
            features |= CoverEntityFeature.STOP
        if ZHACoverEntityFeature.OPEN_TILT in zha_features:
            features |= CoverEntityFeature.OPEN_TILT
        if ZHACoverEntityFeature.CLOSE_TILT in zha_features:
            features |= CoverEntityFeature.CLOSE_TILT
        if ZHACoverEntityFeature.STOP_TILT in zha_features:
            features |= CoverEntityFeature.STOP_TILT
        if ZHACoverEntityFeature.SET_TILT_POSITION in zha_features:
            features |= CoverEntityFeature.SET_TILT_POSITION

        return features