def restore_weights(self, filepath):
    """Load pretrained weights.

    This function loads a .h5 file from the filepath with saved model weights
    and assigns them to the model.

    Args:
      filepath: String, path to the .h5 file

    Raises:
      ValueError: if the file referenced by `filepath` does not exist.
    """
    if not tf.io.gfile.exists(filepath):
      raise ValueError('Unable to load weights from %s. You must provide a'
                       'valid file.' % (filepath))

    # Create a local copy of the weights file for h5py to be able to read it.
    local_filename = os.path.basename(filepath)
    tmp_filename = os.path.join(tempfile.gettempdir(), local_filename)
    tf.io.gfile.copy(filepath, tmp_filename, overwrite=True)

    # Load the content of the weights file.
    f = h5py.File(tmp_filename, mode='r')
    saved_layer_names = [n.decode('utf8') for n in f.attrs['layer_names']]

    try:
      # Iterate through all the layers assuming the max `depth` is 2.
      for layer in self.layers:
        if hasattr(layer, 'layers'):
          for inlayer in layer.layers:
            # Make sure the weights are in the saved model, and that we are in
            # the innermost layer.
            if inlayer.name not in saved_layer_names:
              raise ValueError('Layer %s absent from the pretrained weights.'
                               'Unable to load its weights.' % (inlayer.name))
            if hasattr(inlayer, 'layers'):
              raise ValueError('Layer %s is not a depth 2 layer. Unable to load'
                               'its weights.' % (inlayer.name))
            # Assign the weights in the current layer.
            g = f[inlayer.name]
            weight_names = [n.decode('utf8') for n in g.attrs['weight_names']]
            weight_values = [g[weight_name] for weight_name in weight_names]
            logging.info('Setting the weights for layer %s', inlayer.name)
            inlayer.set_weights(weight_values)
    finally:
      # Clean up the temporary file.
      tf.io.gfile.remove(tmp_filename)