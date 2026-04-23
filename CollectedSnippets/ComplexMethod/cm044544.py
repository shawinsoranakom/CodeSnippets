def _parse_weights(self,
                       layer: keras.models.Model | keras.layers.Layer) -> dict:
        """Recursively pass through sub-models to scan layer weights"""
        weights = layer.get_weights()
        logger.debug("Processing weights for layer '%s', length: '%s'",
                     layer.name, len(weights))

        if not weights:
            logger.debug("Skipping layer with no weights: %s", layer.name)
            return {}

        if hasattr(layer, "layers"):  # Must be a sub-model
            retval = {}
            for lyr in layer.layers:
                info = self._parse_weights(lyr)
                if not info:
                    continue
                retval[lyr.name] = info
            return retval

        nans = sum(np.count_nonzero(np.isnan(w)) for w in weights)
        infs = sum(np.count_nonzero(np.isinf(w)) for w in weights)

        if nans + infs == 0:
            return {}
        return {"nans": nans, "infs": infs}