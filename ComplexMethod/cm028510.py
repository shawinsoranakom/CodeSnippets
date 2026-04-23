def bio_labels_to_spans(self, bio_labels):
    """Gets labels to spans."""
    spans = []
    for i, label in enumerate(bio_labels):
      if label.startswith("B-"):
        spans.append([i, i, label[2:]])
      elif label.startswith("I-"):
        if spans:
          print("Error... I-tag should not start a span")
          spans.append([i, i, label[2:]])
        elif spans[-1][1] != i - 1 or spans[-1][2] != label[2:]:
          print("Error... I-tag not consistent with previous tag")
          spans.append([i, i, label[2:]])
        else:
          spans[-1][1] = i
      elif label.startswith("O"):
        pass
      else:
        assert False, bio_labels
    spans = list(
        filter(lambda x: x[2] in self.label_to_entity_type_index.keys(), spans))
    return spans