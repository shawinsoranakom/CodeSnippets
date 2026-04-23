def gen_1D_indices_offsets(include_last_offset, allpad):
            indices = []
            offsets = []
            cur_offset = 0

            # Make one bag full and one bag empty, for extra coverage
            empty_bag = random.randint(0, num_bags - 1)
            full_bag = empty_bag
            while full_bag == empty_bag:
                full_bag = random.randint(0, num_bags - 1)

            for bag in range(num_bags):
                offsets.append(cur_offset)
                if bag == full_bag:
                    bag_size = max_indices_per_bag
                elif bag == empty_bag:
                    bag_size = 0
                else:
                    bag_size = random.randint(1, max_indices_per_bag - 1)
                indices += [
                    1 if allpad else random.randint(0, num_words - 1)
                    for _ in range(bag_size)
                ]
                cur_offset += bag_size

            # embedding_bag requires first entry of offsets to be 0
            if offsets[0] != 0:
                raise AssertionError(f"Expected offsets[0] == 0, got {offsets[0]}")

            indices = torch.tensor(indices, device=device)

            if include_last_offset:
                offsets.append(indices.size(0))

            offsets = torch.tensor(offsets, device=device)

            return indices, offsets