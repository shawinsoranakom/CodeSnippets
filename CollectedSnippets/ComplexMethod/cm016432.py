def EXECUTE_NORMALIZED(cls, *args, **kwargs) -> NodeOutput:
        to_return = cls.execute(*args, **kwargs)
        if to_return is None:
            to_return = NodeOutput()
        elif isinstance(to_return, NodeOutput):
            pass
        elif isinstance(to_return, tuple):
            to_return = NodeOutput(*to_return)
        elif isinstance(to_return, dict):
            to_return = NodeOutput.from_dict(to_return)
        elif isinstance(to_return, ExecutionBlocker):
            to_return = NodeOutput(block_execution=to_return.message)
        else:
            raise Exception(f"Invalid return type from node: {type(to_return)}")
        if to_return.expand is not None and not cls.SCHEMA.enable_expand:
            raise Exception(f"Node {cls.__name__} is not expandable, but expand included in NodeOutput; developer should set enable_expand=True on node's Schema to allow this.")
        return to_return