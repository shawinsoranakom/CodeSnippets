def load(self) -> kmodels.Model:
        """ Loads the model from disk

        If the predict function is to be called and the model cannot be found in the model folder
        then an error is logged and the process exits.

        When loading the model, the plugin model folder is scanned for custom layers which are
        added to Keras' custom objects.

        Returns
        -------
        :class:`keras.models.Model`
            The saved model loaded from disk
        """
        logger.debug("Loading model: %s", self.filename)
        if self._is_predict and not self.model_exists:
            logger.error("Model could not be found in folder '%s'. Exiting", self._model_dir)
            sys.exit(1)

        try:
            model = kmodels.load_model(self.filename, compile=False)
        except RuntimeError as err:
            if "unable to get link info" in str(err).lower():
                msg = (f"Unable to load the model from '{self.filename}'. This may be a "
                       "temporary error but most likely means that your model has corrupted.\n"
                       "You can try to load the model again but if the problem persists you "
                       "should use the Restore Tool to restore your model from backup.\n"
                       f"Original error: {str(err)}")
                raise FaceswapError(msg) from err
            raise err
        except KeyError as err:
            if "unable to open object" in str(err).lower():
                msg = (f"Unable to load the model from '{self.filename}'. This may be a "
                       "temporary error but most likely means that your model has corrupted.\n"
                       "You can try to load the model again but if the problem persists you "
                       "should use the Restore Tool to restore your model from backup.\n"
                       f"Original error: {str(err)}")
                raise FaceswapError(msg) from err
            if 'parameter name can\\\'t contain "."' in str(err).lower():
                PatchKerasConfig(self.filename)()
                return self.load()
            raise err
        except TypeError as err:
            if any(x in str(err) for x in ("Could not locate class 'Conv2D'",
                                           "Could not locate class 'DepthwiseConv2D'")):
                PatchKerasConfig(self.filename)()
                return self.load()
            raise err

        logger.info("Loaded model from disk: '%s'", self.filename)
        return model