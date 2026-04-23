def setUp(self):
        super().setUp()
        if self.__class__.__name__[-5:] == 'Class':
            class BaseEnum(self.enum_type):
                @enum.property
                def first(self):
                    return '%s is first!' % self.name
            class MainEnum(BaseEnum):
                first = auto()
                second = auto()
                third = auto()
                if issubclass(self.enum_type, Flag):
                    dupe = 3
                else:
                    dupe = third
            self.MainEnum = MainEnum
            #
            class NewStrEnum(self.enum_type):
                def __str__(self):
                    return self.name.upper()
                first = auto()
            self.NewStrEnum = NewStrEnum
            #
            class NewFormatEnum(self.enum_type):
                def __format__(self, spec):
                    return self.name.upper()
                first = auto()
            self.NewFormatEnum = NewFormatEnum
            #
            class NewStrFormatEnum(self.enum_type):
                def __str__(self):
                    return self.name.title()
                def __format__(self, spec):
                    return ''.join(reversed(self.name))
                first = auto()
            self.NewStrFormatEnum = NewStrFormatEnum
            #
            class NewBaseEnum(self.enum_type):
                def __str__(self):
                    return self.name.title()
                def __format__(self, spec):
                    return ''.join(reversed(self.name))
            self.NewBaseEnum = NewBaseEnum
            class NewSubEnum(NewBaseEnum):
                first = auto()
            self.NewSubEnum = NewSubEnum
            #
            class LazyGNV(self.enum_type):
                def _generate_next_value_(name, start, last, values):
                    pass
            self.LazyGNV = LazyGNV
            #
            class BusyGNV(self.enum_type):
                @staticmethod
                def _generate_next_value_(name, start, last, values):
                    pass
            self.BusyGNV = BusyGNV
            #
            self.is_flag = False
            self.names = ['first', 'second', 'third']
            if issubclass(MainEnum, StrEnum):
                self.values = self.names
            elif MainEnum._member_type_ is str:
                self.values = ['1', '2', '3']
            elif issubclass(self.enum_type, Flag):
                self.values = [1, 2, 4]
                self.is_flag = True
                self.dupe2 = MainEnum(5)
            else:
                self.values = self.values or [1, 2, 3]
            #
            if not getattr(self, 'source_values', False):
                self.source_values = self.values
        elif self.__class__.__name__[-8:] == 'Function':
            @enum.property
            def first(self):
                return '%s is first!' % self.name
            BaseEnum = self.enum_type('BaseEnum', {'first':first})
            #
            first = auto()
            second = auto()
            third = auto()
            if issubclass(self.enum_type, Flag):
                dupe = 3
            else:
                dupe = third
            self.MainEnum = MainEnum = BaseEnum('MainEnum', dict(first=first, second=second, third=third, dupe=dupe))
            #
            def __str__(self):
                return self.name.upper()
            first = auto()
            self.NewStrEnum = self.enum_type('NewStrEnum', (('first',first),('__str__',__str__)))
            #
            def __format__(self, spec):
                return self.name.upper()
            first = auto()
            self.NewFormatEnum = self.enum_type('NewFormatEnum', [('first',first),('__format__',__format__)])
            #
            def __str__(self):
                return self.name.title()
            def __format__(self, spec):
                return ''.join(reversed(self.name))
            first = auto()
            self.NewStrFormatEnum = self.enum_type('NewStrFormatEnum', dict(first=first, __format__=__format__, __str__=__str__))
            #
            def __str__(self):
                return self.name.title()
            def __format__(self, spec):
                return ''.join(reversed(self.name))
            self.NewBaseEnum = self.enum_type('NewBaseEnum', dict(__format__=__format__, __str__=__str__))
            self.NewSubEnum = self.NewBaseEnum('NewSubEnum', 'first')
            #
            def _generate_next_value_(name, start, last, values):
                pass
            self.LazyGNV = self.enum_type('LazyGNV', {'_generate_next_value_':_generate_next_value_})
            #
            @staticmethod
            def _generate_next_value_(name, start, last, values):
                pass
            self.BusyGNV = self.enum_type('BusyGNV', {'_generate_next_value_':_generate_next_value_})
            #
            self.is_flag = False
            self.names = ['first', 'second', 'third']
            if issubclass(MainEnum, StrEnum):
                self.values = self.names
            elif MainEnum._member_type_ is str:
                self.values = ['1', '2', '3']
            elif issubclass(self.enum_type, Flag):
                self.values = [1, 2, 4]
                self.is_flag = True
                self.dupe2 = MainEnum(5)
            else:
                self.values = self.values or [1, 2, 3]
            #
            if not getattr(self, 'source_values', False):
                self.source_values = self.values
        else:
            raise ValueError('unknown enum style: %r' % self.__class__.__name__)