def __iter__(self):
                return (attr for attr in dir(TestObject) if attr[:2] != "__")