def _lookup_dense(self, inputs):
        """Lookup table values for a dense Tensor, handling masking and OOV."""
        # When executing eagerly and tracing keras.Input objects,
        # do not call lookup.
        # This is critical for restoring SavedModel, which will first trace
        # layer.call and then attempt to restore the table. We need the table to
        # be uninitialized for the restore to work, but calling the table
        # uninitialized would error.
        if tf.executing_eagerly() and backend.is_keras_tensor(inputs):
            lookups = tf.zeros_like(inputs, dtype=self._value_dtype)
        else:
            lookups = self.lookup_table.lookup(inputs)

        if self.mask_token is not None:
            mask_locations = tf.equal(inputs, self._mask_key)
            lookups = tf.where(mask_locations, self._mask_value, lookups)

        if self.invert:
            return lookups

        lookup_checks = []

        if self.num_oov_indices == 0:
            # If we have zero oov indices, we need to check for oov inputs.
            oov_indices = tf.where(tf.equal(lookups, -1))
            oov_inputs = tf.gather_nd(inputs, oov_indices)
            msg = tf.strings.format(
                "When `num_oov_indices=0` all inputs should be in vocabulary, "
                "found OOV values {}, consider setting `num_oov_indices=1`.",
                (oov_inputs,),
            )
            assertion = tf.Assert(tf.equal(tf.size(oov_indices), 0), [msg])
            lookup_checks.append(assertion)

        elif self.num_oov_indices > 1:
            if (
                tf.as_dtype(self._key_dtype).is_integer
                and self.oov_method != "farmhash"
            ):
                # Default: backwards-compatible floormod behaviour for integers.
                oov_indices = tf.math.floormod(inputs, self.num_oov_indices)
            else:
                # Hashing with`oov_method="farmhash"`.
                hash_inputs = inputs
                if tf.as_dtype(self._key_dtype).is_integer:
                    hash_inputs = tf.strings.as_string(inputs)

                if self.salt is not None:
                    # SipHash64
                    oov_indices = tf.strings.to_hash_bucket_strong(
                        hash_inputs,
                        num_buckets=self.num_oov_indices,
                        key=self.salt,
                    )
                else:
                    # FarmHash64
                    oov_indices = tf.strings.to_hash_bucket_fast(
                        hash_inputs,
                        num_buckets=self.num_oov_indices,
                    )
            oov_indices = oov_indices + self._oov_start_index()
            oov_locations = tf.equal(lookups, self._default_value)
            lookups = tf.where(oov_locations, oov_indices, lookups)

        with tf.control_dependencies(lookup_checks):
            return tf.identity(lookups)