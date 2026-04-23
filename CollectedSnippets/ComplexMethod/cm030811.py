def test_type_specific_attributes_removed_on_conversion(self):
        reference = {class_: class_(_sample_message).__dict__
                        for class_ in self.all_mailbox_types}
        for class1 in self.all_mailbox_types:
            for class2 in self.all_mailbox_types:
                if class1 is class2:
                    continue
                source = class1(_sample_message)
                target = class2(source)
                type_specific = [a for a in reference[class1]
                                   if a not in reference[class2]]
                for attr in type_specific:
                    self.assertNotIn(attr, target.__dict__,
                        "while converting {} to {}".format(class1, class2))