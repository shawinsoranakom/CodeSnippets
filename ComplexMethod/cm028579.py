def apply_transform(i, x, brightness, contrast, saturation, hue):
      """Apply the i-th transformation."""
      if brightness != 0 and i == 0:
        x = random_brightness(x, max_delta=brightness, impl=impl)
      elif contrast != 0 and i == 1:
        x = tf.image.random_contrast(
            x, lower=1 - contrast, upper=1 + contrast)
      elif saturation != 0 and i == 2:
        x = tf.image.random_saturation(
            x, lower=1 - saturation, upper=1 + saturation)
      elif hue != 0:
        x = tf.image.random_hue(x, max_delta=hue)
      return x