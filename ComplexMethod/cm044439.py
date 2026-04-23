def _get_layers(self) -> list[layers.Layer]:
        """ Obtain the layer chain for the block

        Returns
        -------
        list[:class:`keras.layers.Layer]
            The layers, in the correct order, to pass the tensor through
        """
        retval = []
        if self._use_reflect_padding:
            retval.append(ReflectionPadding2D(stride=self._strides[0],
                                              kernel_size=self._args[-1][0],  # type:ignore[index]
                                              name=f"{self._name}_reflectionpadding2d"))

        conv: layers.Layer = (
            DepthwiseConv2D if self._use_depthwise
            else Conv2D)  # pyright:ignore[reportAssignmentType]

        retval.append(conv(*self._args,
                           strides=self._strides,
                           padding=self._padding,
                           name=f"{self._name}_{'dw' if self._use_depthwise else ''}conv2d",
                           **self._kwargs))

        # normalization
        if self._normalization == "instance":
            retval.append(InstanceNormalization(name=f"{self._name}_instancenorm"))

        if self._normalization == "batch":
            retval.append(layers.BatchNormalization(axis=3, name=f"{self._name}_batchnorm"))

        # activation
        if self._activation == "leakyrelu":
            retval.append(layers.LeakyReLU(self._relu_alpha, name=f"{self._name}_leakyrelu"))
        if self._activation == "swish":
            retval.append(Swish(name=f"{self._name}_swish"))
        if self._activation == "prelu":
            retval.append(layers.PReLU(name=f"{self._name}_prelu"))

        logger.debug("%s layers: %s", self.__class__.__name__, retval)
        return retval