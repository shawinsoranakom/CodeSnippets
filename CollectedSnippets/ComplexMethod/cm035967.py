def __init__(self, **kwargs):
        # Serialize Pydantic model objects to dicts for JSON columns.
        from pydantic import BaseModel

        for key in ('agent_settings', 'conversation_settings'):
            if key in kwargs and isinstance(kwargs[key], BaseModel):
                kwargs[key] = kwargs[key].model_dump(mode='json')

        # Handle known SQLAlchemy columns directly
        for key in list(kwargs):
            if hasattr(self.__class__, key):
                setattr(self, key, kwargs.pop(key))

        # Handle custom property-style fields
        if 'llm_api_key' in kwargs:
            self.llm_api_key = kwargs.pop('llm_api_key')
        if 'search_api_key' in kwargs:
            self.search_api_key = kwargs.pop('search_api_key')
        if 'sandbox_api_key' in kwargs:
            self.sandbox_api_key = kwargs.pop('sandbox_api_key')

        if kwargs:
            raise TypeError(f'Unexpected keyword arguments: {list(kwargs.keys())}')