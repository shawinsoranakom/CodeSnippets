def _test_shuffle(self, loader):
        found_data = dict.fromkeys(range(self.data.size(0)), 0)
        found_labels = dict.fromkeys(range(self.labels.size(0)), 0)
        batch_size = loader.batch_size
        if batch_size is None:
            for i, (batch_samples, batch_targets) in enumerate(loader):
                sample, target = (batch_samples, batch_targets)
                for data_point_idx, data_point in enumerate(self.data):
                    if data_point.eq(sample).all():
                        self.assertFalse(found_data[data_point_idx])
                        found_data[data_point_idx] += 1
                        break
                self.assertEqual(target, self.labels[data_point_idx])
                found_labels[data_point_idx] += 1
                self.assertEqual(sum(found_data.values()), (i + 1))
                self.assertEqual(sum(found_labels.values()), (i + 1))
            self.assertEqual(i, (len(self.dataset) - 1))
        else:
            for i, (batch_samples, batch_targets) in enumerate(loader):
                for sample, target in zip(batch_samples, batch_targets):
                    for data_point_idx, data_point in enumerate(self.data):
                        if data_point.eq(sample).all():
                            self.assertFalse(found_data[data_point_idx])
                            found_data[data_point_idx] += 1
                            break
                    self.assertEqual(target, self.labels[data_point_idx])
                    found_labels[data_point_idx] += 1
                self.assertEqual(sum(found_data.values()), (i + 1) * batch_size)
                self.assertEqual(sum(found_labels.values()), (i + 1) * batch_size)
            self.assertEqual(i, math.floor((len(self.dataset) - 1) / batch_size))