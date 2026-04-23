def compute_packed(self, order):
        def compute_chunk(node, offsets):
            """ compute the packed node/edge data for a node. result is a
            list of bytes as long as order. the jump distance calculations use
            the offsets dictionary to know where in the final big output
            bytestring the individual nodes will end up. """
            result = bytearray()
            offset = offsets[node]
            encode_varint_unsigned(number_add_bits(node.num_reachable_linear, node.final), result)
            if len(node.linear_edges) == 0:
                assert node.final
                encode_varint_unsigned(0, result) # add a 0 saying "done"
            prev_child_offset = offset + len(result)
            for edgeindex, (label, targetnode) in enumerate(node.linear_edges):
                label = label.encode('ascii')
                child_offset = offsets[targetnode]
                child_offset_difference = child_offset - prev_child_offset

                info = number_add_bits(child_offset_difference, len(label) == 1, edgeindex == len(node.linear_edges) - 1)
                if edgeindex == 0:
                    assert info != 0
                encode_varint_unsigned(info, result)
                prev_child_offset = child_offset
                if len(label) > 1:
                    encode_varint_unsigned(len(label), result)
                result.extend(label)
            return result

        def compute_new_offsets(chunks, offsets):
            """ Given a list of chunks, compute the new offsets (by adding the
            chunk lengths together). Also check if we cannot shrink the output
            further because none of the node offsets are smaller now. if that's
            the case return None. """
            new_offsets = {}
            curr_offset = 0
            should_continue = False
            for node, result in zip(order, chunks):
                if curr_offset < offsets[node]:
                    # the new offset is below the current assumption, this
                    # means we can shrink the output more
                    should_continue = True
                new_offsets[node] = curr_offset
                curr_offset += len(result)
            if not should_continue:
                return None
            return new_offsets

        # assign initial offsets to every node
        offsets = {}
        for i, node in enumerate(order):
            # we don't know position of the edge yet, just use something big as
            # the starting position. we'll have to do further iterations anyway,
            # but the size is at least a lower limit then
            offsets[node] = i * 2 ** 30


        # due to the variable integer width encoding of edge targets we need to
        # run this to fixpoint. in the process we shrink the output more and
        # more until we can't any more. at any point we can stop and use the
        # output, but we might need padding zero bytes when joining the chunks
        # to have the correct jump distances
        last_offsets = None
        while 1:
            chunks = [compute_chunk(node, offsets) for node in order]
            last_offsets = offsets
            offsets = compute_new_offsets(chunks, offsets)
            if offsets is None: # couldn't shrink
                break

        # build the final packed string
        total_result = bytearray()
        for node, result in zip(order, chunks):
            node_offset = last_offsets[node]
            if node_offset > len(total_result):
                # need to pad to get the offsets correct
                padding = b"\x00" * (node_offset - len(total_result))
                total_result.extend(padding)
            assert node_offset == len(total_result)
            total_result.extend(result)
        return bytes(total_result)