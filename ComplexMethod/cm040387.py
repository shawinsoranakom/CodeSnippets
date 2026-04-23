def loop_body(i, carry_array, ys_array):
        packed_xs = (
            pack_input([xs.read(i) for xs in xs_array])
            if len(xs_array) > 0
            else None
        )
        packed_carry = pack_output([carry.read(0) for carry in carry_array])

        carry, ys = f(packed_carry, packed_xs)

        if ys is not None:
            flat_ys = tree.flatten(ys)
            ys_array = [ys.write(i, v) for (ys, v) in zip(ys_array, flat_ys)]
        if carry is not None:
            flat_carry = tree.flatten(carry)
            carry_array = [
                carry.write(0, v) for (carry, v) in zip(carry_array, flat_carry)
            ]
        next_i = i + 1 if not reverse else i - 1
        return (next_i, carry_array, ys_array)