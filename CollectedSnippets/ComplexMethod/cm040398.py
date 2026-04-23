def einsum(subscripts, *operands, **kwargs):
    operands = tree.map_structure(convert_to_tensor, operands)
    subscripts = _normalize_einsum_subscripts(subscripts)

    def is_valid_for_custom_ops(subscripts, *operands):
        # Check that `subscripts` is supported and the shape of operands is not
        # `None`.
        if subscripts in [
            "a,b->ab",
            "ab,b->a",
            "ab,bc->ac",
            "ab,cb->ac",
            "abc,cd->abd",
            "abc,dc->abd",
            "abcd,abde->abce",
            "abcd,abed->abce",
            "abcd,acbe->adbe",
            "abcd,adbe->acbe",
            "abcd,aecd->acbe",
            "abcd,aecd->aceb",
        ]:
            # These subscripts don't require the shape information
            return True
        elif subscripts == "abc,cde->abde":
            _, b1, c1 = operands[0].shape
            c2, d2, e2 = operands[1].shape
            b, c, d, e = b1, c1 or c2, d2, e2
            if None in (b, c, d, e):
                return False
            return True
        elif subscripts == "abc,dce->abde":
            _, b1, c1 = operands[0].shape
            d2, c2, e2 = operands[1].shape
            b, c, d, e = b1, c1 or c2, d2, e2
            if None in (b, c, d, e):
                return False
            return True
        elif subscripts == "abc,dec->abde":
            _, b1, c1 = operands[0].shape
            d2, e2, c2 = operands[1].shape
            b, c, d, e = b1, c1 or c2, d2, e2
            if None in (b, c, d, e):
                return False
            return True
        elif subscripts == "abcd,cde->abe":
            _, b1, c1, d1 = operands[0].shape
            c2, d2, e2 = operands[1].shape
            b, c, d, e = b1, c1 or c2, d1 or d2, e2
            if None in (b, c, d, e):
                return False
            return True
        elif subscripts == "abcd,ced->abe":
            _, b1, c1, d1 = operands[0].shape
            c2, e2, d2 = operands[1].shape
            b, c, d, e = b1, c1 or c2, d1 or d2, e2
            if None in (b, c, d, e):
                return False
            return True
        elif subscripts == "abcd,ecd->abe":
            _, b1, c1, d1 = operands[0].shape
            e2, c2, d2 = operands[1].shape
            b, c, d, e = b1, c1 or c2, d1 or d2, e2
            if None in (b, c, d, e):
                return False
            return True
        elif subscripts == "abcde,aebf->adbcf":
            _, b1, c1, d1, e1 = operands[0].shape
            _, e2, b2, f2 = operands[1].shape
            b, c, d, e, f = b1 or b2, c1, d1, e1 or e2, f2
            if None in (b, c, d, e, f):
                return False
            return True
        elif subscripts == "abcde,afce->acdbf":
            _, b1, c1, d1, e1 = operands[0].shape
            _, f2, c2, e2 = operands[1].shape
            b, c, d, e, f = b1, c1 or c2, d1, e1 or e2, f2
            if None in (b, c, d, e, f):
                return False
            return True
        else:
            # No match in subscripts
            return False

    def use_custom_ops(subscripts, *operands, output_type):
        # Replace tf.einsum with custom ops to utilize hardware-accelerated
        # matmul
        x, y = operands[0], operands[1]
        if subscripts == "a,b->ab":
            x = tf.expand_dims(x, axis=-1)
            y = tf.expand_dims(y, axis=0)
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "ab,b->a":
            y = tf.expand_dims(y, axis=-1)
            result = tf.matmul(x, y, output_type=output_type)
            return tf.squeeze(result, axis=-1)
        elif subscripts == "ab,bc->ac":
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "ab,cb->ac":
            y = tf.transpose(y, [1, 0])
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abc,cd->abd":
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abc,cde->abde":
            _, b1, c1 = x.shape
            c2, d2, e2 = y.shape
            b, c, d, e = b1, c1 or c2, d2, e2
            y = tf.reshape(y, [c, -1])
            result = tf.matmul(x, y, output_type=output_type)
            return tf.reshape(result, [-1, b, d, e])
        elif subscripts == "abc,dc->abd":
            y = tf.transpose(y, [1, 0])
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abc,dce->abde":
            _, b1, c1 = x.shape
            d2, c2, e2 = y.shape
            b, c, d, e = b1, c1 or c2, d2, e2
            y = tf.transpose(y, [1, 0, 2])  # cde
            y = tf.reshape(y, [c, -1])
            result = tf.matmul(x, y, output_type=output_type)
            return tf.reshape(result, [-1, b, d, e])
        elif subscripts == "abc,dec->abde":
            _, b1, c1 = x.shape
            d2, e2, c2 = y.shape
            b, c, d, e = b1, c1 or c2, d2, e2
            y = tf.transpose(y, [2, 0, 1])  # cde
            y = tf.reshape(y, [c, -1])
            result = tf.matmul(x, y, output_type=output_type)
            return tf.reshape(result, [-1, b, d, e])
        elif subscripts == "abcd,abde->abce":
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abcd,abed->abce":
            y = tf.transpose(y, [0, 1, 3, 2])
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abcd,acbe->adbe":
            x = tf.transpose(x, [0, 1, 3, 2])
            y = tf.transpose(y, [0, 2, 1, 3])
            result = tf.matmul(x, y, output_type=output_type)
            return tf.transpose(result, [0, 2, 1, 3])
        elif subscripts == "abcd,adbe->acbe":
            y = tf.transpose(y, [0, 2, 1, 3])  # abde
            result = tf.matmul(x, y, output_type=output_type)  # abce
            return tf.transpose(result, [0, 2, 1, 3])
        elif subscripts == "abcd,aecd->acbe":
            x = tf.transpose(x, [0, 2, 1, 3])  # acbd
            y = tf.transpose(y, [0, 2, 3, 1])  # acde
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abcd,aecd->aceb":
            x = tf.transpose(x, [0, 2, 1, 3])
            y = tf.transpose(y, [0, 2, 3, 1])
            result = tf.matmul(x, y, output_type=output_type)  # acbe
            return tf.transpose(result, [0, 1, 3, 2])
        elif subscripts == "abcd,cde->abe":
            _, b1, c1, d1 = x.shape
            c2, d2, e2 = y.shape
            b, c, d, e = b1, c1 or c2, d1 or d2, e2
            x = tf.reshape(x, [-1, b, c * d])
            y = tf.reshape(y, [-1, e])
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abcd,ced->abe":
            _, b1, c1, d1 = x.shape
            c2, e2, d2 = y.shape
            b, c, d, e = b1, c1 or c2, d1 or d2, e2
            x = tf.reshape(x, [-1, b, c * d])
            y = tf.transpose(y, [0, 2, 1])
            y = tf.reshape(y, [-1, e])
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abcd,ecd->abe":
            _, b1, c1, d1 = x.shape
            e2, c2, d2 = y.shape
            b, c, d, e = b1, c1 or c2, d1 or d2, e2
            x = tf.reshape(x, [-1, b, c * d])
            y = tf.transpose(y, [1, 2, 0])
            y = tf.reshape(y, [-1, e])
            return tf.matmul(x, y, output_type=output_type)
        elif subscripts == "abcde,aebf->adbcf":
            _, b1, c1, d1, e1 = x.shape
            _, e2, b2, f2 = y.shape
            b, c, d, e, f = b1 or b2, c1, d1, e1 or e2, f2
            x = tf.reshape(x, [-1, b, c * d, e])  # ab(cd)e
            y = tf.transpose(y, [0, 2, 1, 3])  # abef
            result = tf.matmul(x, y, output_type=output_type)  # ab(cd)f
            result = tf.reshape(result, [-1, b, c, d, f])  # abcdf
            return tf.transpose(result, [0, 3, 1, 2, 4])
        elif subscripts == "abcde,afce->acdbf":
            _, b1, c1, d1, e1 = x.shape
            _, f2, c2, e2 = y.shape
            b, c, d, e, f = b1, c1 or c2, d1, e1 or e2, f2
            x = tf.transpose(x, [0, 2, 3, 1, 4])  # acdbe
            x = tf.reshape(x, [-1, c, d * b, e])  # ac(db)e
            y = tf.transpose(y, [0, 2, 3, 1])  # acef
            result = tf.matmul(x, y, output_type=output_type)  # ac(db)f
            return tf.reshape(result, [-1, c, d, b, f])
        else:
            raise NotImplementedError

    dtypes_to_resolve = list(set(standardize_dtype(x.dtype) for x in operands))
    # When operands are of int8, we cast the result to int32 to align with
    # the behavior of jax.
    if len(dtypes_to_resolve) == 1 and dtypes_to_resolve[0] == "int8":
        compute_dtype = "int8"
        result_dtype = "int32"
        output_type = "int32"
    else:
        result_dtype = dtypes.result_type(*dtypes_to_resolve)
        compute_dtype = result_dtype
        output_type = None

    # TODO: Remove the condition once `tf.einsum` supports int8xint8->int32
    if is_valid_for_custom_ops(subscripts, *operands) and not kwargs:
        # TODO: tf.matmul doesn't support integer dtype if not specifying
        # output_type="int32"
        if "int" in compute_dtype and output_type is None:
            compute_dtype = config.floatx()
        operands = tree.map_structure(
            lambda x: tf.cast(x, compute_dtype), operands
        )
        result = use_custom_ops(subscripts, *operands, output_type=output_type)
    else:
        # TODO: tf.einsum doesn't support integer dtype with gpu
        if "int" in compute_dtype:
            compute_dtype = config.floatx()
        operands = tree.map_structure(
            lambda x: tf.cast(x, compute_dtype), operands
        )
        result = tf.einsum(subscripts, *operands, **kwargs)
    return tf.cast(result, result_dtype)