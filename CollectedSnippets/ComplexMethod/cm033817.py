def get_ansible_module(self, node: astroid.nodes.AssignAttr) -> astroid.bases.Instance | None:
        """Infer an AnsibleModule instance node from the given assignment."""
        if isinstance(node.parent, astroid.nodes.Assign) and isinstance(node.parent.type_annotation, astroid.nodes.Name):
            inferred = self.infer_name(node.parent.type_annotation)
        elif (isinstance(node.parent, astroid.nodes.Assign) and isinstance(node.parent.parent, astroid.nodes.FunctionDef) and
              isinstance(node.parent.value, astroid.nodes.Name)):
            inferred = self.infer_name(node.parent.value)
        elif isinstance(node.parent, astroid.nodes.AnnAssign) and isinstance(node.parent.annotation, astroid.nodes.Name):
            inferred = self.infer_name(node.parent.annotation)
        else:
            inferred = None

        if isinstance(inferred, astroid.nodes.ClassDef) and inferred.name == 'AnsibleModule':
            return inferred.instantiate_class()

        return None