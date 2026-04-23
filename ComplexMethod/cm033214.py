def create_dataset_table(self, items):
        dataset_name = None
        vector_size = None
        for i, item in enumerate(items):
            if hasattr(item, 'data') and item.data == 'quoted_string':
                dataset_name = item.children[0].strip("'\"")
            if hasattr(item, 'type') and item.type == 'NUMBER':
                if i > 0 and items[i-1].type == 'SIZE' and items[i-2].type == 'VECTOR':
                    vector_size = int(item)
        return {"type": "create_dataset_table", "dataset_name": dataset_name, "vector_size": vector_size}