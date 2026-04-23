def get_size_with_aspect_ratio(image_size, size, max_size=None):
    h = image_size[0]
    w = image_size[1]
    if max_size is not None:
      min_original_size = tf.cast(tf.math.minimum(w, h), dtype=tf.float32)
      max_original_size = tf.cast(tf.math.maximum(w, h), dtype=tf.float32)
      if max_original_size / min_original_size * size > max_size:
        size = tf.cast(
            tf.math.floor(max_size * min_original_size / max_original_size),
            dtype=tf.int32,
        )
      else:
        size = tf.cast(size, tf.int32)

    else:
      size = tf.cast(size, tf.int32)
    if (w <= h and w == size) or (h <= w and h == size):
      return tf.stack([h, w])

    if w < h:
      ow = size
      oh = tf.cast(
          (
              tf.cast(size, dtype=tf.float32)
              * tf.cast(h, dtype=tf.float32)
              / tf.cast(w, dtype=tf.float32)
          ),
          dtype=tf.int32,
      )
    else:
      oh = size
      ow = tf.cast(
          (
              tf.cast(size, dtype=tf.float32)
              * tf.cast(w, dtype=tf.float32)
              / tf.cast(h, dtype=tf.float32)
          ),
          dtype=tf.int32,
      )

    return tf.stack([oh, ow])