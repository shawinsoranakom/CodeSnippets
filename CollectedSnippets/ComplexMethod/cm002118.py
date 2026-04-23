def test_checkpoint_sharding_local(self):
        model = BertModel.from_pretrained("hf-internal-testing/tiny-random-bert")

        with tempfile.TemporaryDirectory() as tmp_dir:
            # We use the same folder for various sizes to make sure a new save erases the old checkpoint.
            for max_size in ["50kB", "100kB", "200kB"]:
                model.save_pretrained(tmp_dir, max_shard_size=max_size)

                # Get each shard file and its size
                shard_to_size = {}
                for shard in os.listdir(tmp_dir):
                    if shard.endswith(".safetensors"):
                        shard_file = os.path.join(tmp_dir, shard)
                        shard_to_size[shard_file] = os.path.getsize(shard_file)

                index_file = os.path.join(tmp_dir, SAFE_WEIGHTS_INDEX_NAME)
                # Check there is an index but no regular weight file
                self.assertTrue(os.path.isfile(index_file))
                self.assertFalse(os.path.isfile(os.path.join(tmp_dir, SAFE_WEIGHTS_NAME)))

                # Check a file is bigger than max_size only when it has a single weight
                for shard_file, size in shard_to_size.items():
                    max_size_int = int(max_size[:-2]) * 10**3
                    # Note: the file can end up being slightly bigger than the size asked for (since we count parameters)
                    if size >= max_size_int + 50000:
                        state_dict = load_file(shard_file)
                        self.assertEqual(len(state_dict), 1)

                # Check the index and the shard files found match
                with open(index_file, encoding="utf-8") as f:
                    index = json.loads(f.read())

                all_shards = set(index["weight_map"].values())
                shards_found = {f for f in os.listdir(tmp_dir) if f.endswith(".safetensors")}
                self.assertSetEqual(all_shards, shards_found)

                # Finally, check the model can be reloaded
                new_model = BertModel.from_pretrained(tmp_dir)
                for p1, p2 in zip(model.parameters(), new_model.parameters()):
                    torch.testing.assert_close(p1, p2)