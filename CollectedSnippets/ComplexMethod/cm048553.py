def assertNodeDictEqual(node_dict, expected_node_dict):
            ''' Compare nodes created by the `_turn_node_as_dict_hierarchy` method.
            :param node_dict:           The node to compare with.
            :param expected_node_dict:  The expected node.
            '''
            if expected_node_dict['text'] == '___ignore___':
                return
            # Check tag.
            self.assertEqual(node_dict['tag'], expected_node_dict['tag'])

            # Check attributes.
            for k, v in expected_node_dict['attrib'].items():
                if v == '___ignore___':
                    node_dict['attrib'][k] = '___ignore___'

            self.assertDictEqual(
                node_dict['attrib'],
                expected_node_dict['attrib'],
                f"Element attributes are different for node {node_dict['full_path']}",
            )

            # Check text.
            if expected_node_dict['text'] != '___ignore___':
                self.assertEqual(
                    node_dict['text'],
                    expected_node_dict['text'],
                    f"Element text are different for node {node_dict['full_path']}",
                )

            # Check children.
            children = [child['tag'] for child in node_dict['children']]
            expected_children = [child['tag'] for child in expected_node_dict['children']]
            if children != expected_children:
                for child in node_dict['children']:
                    if child['tag'] not in expected_children:
                        _logger.warning('Non-expected child: \n%s', etree.tostring(child['node']).decode())
                for child in expected_node_dict['children']:
                    if child['tag'] not in children:
                        _logger.warning('Missing child: \n%s', etree.tostring(child['node']).decode())

            self.assertEqual(
                children,
                expected_children,
                f"Number of children elements for node {node_dict['full_path']} is different.",
            )

            for child_node_dict, expected_child_node_dict in zip(node_dict['children'], expected_node_dict['children']):
                assertNodeDictEqual(child_node_dict, expected_child_node_dict)