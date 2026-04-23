def test_traversal_xml_etree(self):
        etree = xml.etree.ElementTree.fromstring('''<?xml version="1.0"?>
        <data>
            <country name="Liechtenstein">
                <rank>1</rank>
                <year>2008</year>
                <gdppc>141100</gdppc>
                <neighbor name="Austria" direction="E"/>
                <neighbor name="Switzerland" direction="W"/>
            </country>
            <country name="Singapore">
                <rank>4</rank>
                <year>2011</year>
                <gdppc>59900</gdppc>
                <neighbor name="Malaysia" direction="N"/>
            </country>
            <country name="Panama">
                <rank>68</rank>
                <year>2011</year>
                <gdppc>13600</gdppc>
                <neighbor name="Costa Rica" direction="W"/>
                <neighbor name="Colombia" direction="E"/>
            </country>
        </data>''')
        assert traverse_obj(etree, '') == etree, \
            'empty str key should return the element itself'
        assert traverse_obj(etree, 'country') == list(etree), \
            'str key should lead all children with that tag name'
        assert traverse_obj(etree, ...) == list(etree), \
            '`...` as key should return all children'
        assert traverse_obj(etree, lambda _, x: x[0].text == '4') == [etree[1]], \
            'function as key should get element as value'
        assert traverse_obj(etree, lambda i, _: i == 1) == [etree[1]], \
            'function as key should get index as key'
        assert traverse_obj(etree, 0) == etree[0], \
            'int key should return the nth child'
        expected = ['Austria', 'Switzerland', 'Malaysia', 'Costa Rica', 'Colombia']
        assert traverse_obj(etree, './/neighbor/@name') == expected, \
            '`@<attribute>` at end of path should give that attribute'
        assert traverse_obj(etree, '//neighbor/@fail') == [None, None, None, None, None], \
            '`@<nonexistant>` at end of path should give `None`'
        assert traverse_obj(etree, ('//neighbor/@', 2)) == {'name': 'Malaysia', 'direction': 'N'}, \
            '`@` should give the full attribute dict'
        assert traverse_obj(etree, '//year/text()') == ['2008', '2011', '2011'], \
            '`text()` at end of path should give the inner text'
        assert traverse_obj(etree, '//*[@direction]/@direction') == ['E', 'W', 'N', 'W', 'E'], \
            'full Python xpath features should be supported'
        assert traverse_obj(etree, (0, '@name')) == 'Liechtenstein', \
            'special transformations should act on current element'
        assert traverse_obj(etree, ('country', 0, ..., 'text()', {int_or_none})) == [1, 2008, 141100], \
            'special transformations should act on current element'