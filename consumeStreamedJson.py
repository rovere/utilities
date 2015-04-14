#!/usr/bin/python
"""
File: json_xml_tests.py
Author: Valentin Kuznetsov <vkuznet@gmail.com>
Description: 
"""
import time, sys, os, types, resource, re, gc
import xml.etree.cElementTree as ET
from   types import GeneratorType, InstanceType
try:
    import DAS.utils.jsonwrapper as json
except:
    import cjson

float_number_pattern = \
    re.compile(r'(^[-]?\d+\.\d*$|^\d*\.{1,1}\d+$)')
int_number_pattern = \
    re.compile(r'(^[0-9-]$|^[0-9-][0-9]*$)')

def adjust_value(value):
    """Type conversion helper"""
    pat_float   = float_number_pattern
    pat_integer = int_number_pattern
    if  isinstance(value, str):
        if  value == 'null' or value == '(null)':
            return None
        elif pat_float.match(value):
            return float(value)
        elif pat_integer.match(value):
            return int(value)
        else:
            return value
    else:
        return value

def dict_helper(idict, notations):
    """
    Create new dict for provided notations/dict. Perform implicit conversion
    of data types, e.g. if we got '123', convert it to integer. The conversion
    is done based on adjust_value function.
    """
    #try:
    #    from DAS.extensions.das_speed_utils import _dict_handler
    #    return _dict_handler(idict, notations)
    #except:
    if True:
        child_dict = {}
        for kkk, vvv in idict.items():
            child_dict[notations.get(kkk, kkk)] = adjust_value(vvv)
        return child_dict

def xml_parser(source, prim_key, tags=None):
    """
    XML parser based on ElementTree module. To reduce memory footprint for
    large XML documents we use iterparse method to walk through provided
    source descriptor (a .read()/close()-supporting file-like object 
    containig XML source).

    The provided prim_key defines a tag to capture, while supplementary
    *tags* list defines additional tags which can be added to outgoing
    result. For instance, file object shipped from PhEDEx is enclosed
    into block one, so we want to capture block.name together with
    file object.
    """
    notations = {}
    sup       = {}
    context   = ET.iterparse(source, events=("start", "end"))
    root      = None
    for item in context:
        event, elem = item
        if  event == "start" and root is None:
            root = elem # the first element is root
        row = {}
        if  tags and not sup:
            for tag in tags:
                if  tag.find(".") != -1:
                    atag, attr = tag.split(".")
                    if  elem.tag == atag and elem.attrib.has_key(attr):
                        att_value = elem.attrib[attr]
                        if  isinstance(att_value, dict):
                            att_value = \
                                dict_helper(elem.attrib[attr], notations)
                        if  isinstance(att_value, str):
                            att_value = adjust_value(att_value)
                        sup[atag] = {attr:att_value}
                else:
                    if  elem.tag == tag:
                        sup[tag] = elem.attrib
        key = elem.tag
        if  key != prim_key:
            continue
        row[key] = dict_helper(elem.attrib, notations)
        row[key].update(sup)
        get_children(elem, event, row, key, notations)
        if  event == 'end':
            elem.clear()
            yield row
    root.clear()
    source.close()

def get_children(elem, event, row, key, notations):
    """
    xml_parser helper function. It gets recursively information about
    children for given element tag. Information is stored into provided
    row for given key. The change of notations can be applied during
    parsing step by using provided notations dictionary.
    """
    for child in elem.getchildren():
        child_key  = child.tag
        child_data = child.attrib
        if  not child_data:
            child_dict = adjust_value(child.text)
        else:
            child_dict = dict_helper(child_data, notations)

        if  isinstance(row[key], dict) and row[key].has_key(child_key):
            val = row[key][child_key]
            if  isinstance(val, list):
                val.append(child_dict)
                row[key][child_key] = val
            else:
                row[key][child_key] = [val] + [child_dict]
        else:
            if  child.getchildren(): # we got grand-children
                if  child_dict:
                    row[key][child_key] = child_dict
                else:
                    row[key][child_key] = {}
                if  isinstance(child_dict, dict):
                    newdict = {child_key: child_dict}
                else:
                    newdict = {child_key: {}}
                get_children(child, event, newdict, child_key, notations) 
                row[key][child_key] = newdict[child_key]
            else:
                if  not isinstance(row[key], dict):
                    row[key] = {}
                row[key][child_key] = child_dict
        if  event == 'end':
            child.clear()

def json_parser(source, logger=None):
    """
    JSON parser based on json module. It accepts either source
    descriptor with .read()-supported file-like object or
    data as a string object.
    """
    if  isinstance(source, InstanceType) or isinstance(source, file):
        # got data descriptor
        try:
            jsondict = cjson.decode(source.read())
        except Exception as exc:
            print_exc(exc)
            source.close()
            raise
        source.close()
    else:
        data = source
        # to prevent unicode/ascii errors like
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xbf in position
        # if  isinstance(data, str):
        #    data = unicode(data, errors='ignore')
        #    res  = data.replace('null', '\"null\"')
        #else:
        res  = data
        try:
            jsondict = cjson.decode(res)
        except:
            msg  = "json_parser, WARNING: fail to JSON'ify data:"
            msg += "\n%s\ndata type %s" % (res, type(res))
            if  logger:
                logger.warning(msg)
            else:
                print msg
            jsondict = eval(res, { "__builtins__": None }, {})
    yield jsondict

def sjson_parser(source, logger=None):
    """
    SJSON parser based on cjson module. Reads data line by line in
    streaming json format.
    """
    obj = None
    for line in source:
      if not obj:
        obj = cjson.decode(line + "]}")
      elif line.startswith("]"):
        break
      else:
        o = cjson.decode(line[1:])
        yield o

def test(msg, stream, parser, *args):
    print '\n', msg
    pid = os.getpid()
    before = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.time()
    print "initial layout: rss", before.ru_maxrss
    gen = parser(stream, *args)
    for row in gen:
        pass
    after = resource.getrusage(resource.RUSAGE_SELF)
    print "after: rss", after.ru_maxrss, "drss", (after.ru_maxrss-before.ru_maxrss)/(1024.**2), "time", time.time()-t0

def main():
    # test JSON
    for fname in sys.argv:
      if fname.endswith(".json"):
        with open(fname, 'r') as stream:
          test('JSON test', stream, json_parser, ())
      elif fname.endswith(".sjson"):
        with open(fname, 'r') as stream:
          test('SJSON test', stream, sjson_parser, ())
      elif fname.endswith(".xml"):
        with open(fname, 'r') as stream:
          test('XML test', stream, xml_parser, ('block'))

if __name__ == '__main__':
    gc.set_threshold(128*1024)
    main()

