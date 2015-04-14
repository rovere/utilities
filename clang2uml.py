#!/usr/bin/env python

import sys, os, re
import clang.cindex
import clang.enumerations
from re import match

access_specifiers = ["", "public", "protected", "private"]
access_specifiers_UML = ["", "+", "#", "-"]

def verbose(*args, **kwargs):
    '''filter predicate for show_ast: show all'''
    return True
def no_system_includes(cursor, level):
    '''filter predicate for show_ast: filter out verbose stuff from system include files'''
    return True
    return (level!= 1) or (cursor.location.file is not None and not cursor.location.file.name.startswith('/usr/include/') and not cursor.location.file.name.find('../include/c++/') != -1)

# A function show(level, *args) would have been simpler but less fun
# and you'd need a separate parameter for the AST walkers if you want it to be exchangeable.
class Level(int):
    '''represent currently visited level of a tree'''
    def show(self, *args):
        '''pretty print an indented line'''
        print '\t'*self + ' '.join(map(str, args))
    def __add__(self, inc):
        '''increase level'''
        return Level(super(Level, self).__add__(inc))
    def open(self, type, location, **kwargs):
        '''Opens an XML tag'''
        attributes = {
            "file" : location.file,
            "line" : location.line,
            "column" : location.column,
            }
        attributes.update(kwargs)
        print str(self) + '\t'*self + '<%s %s>' % (type, ' '.join(['%s="%s"' % (key, value) for key, value in attributes.items()]))
    def close(self, type):
        '''Closes an XML tag'''
        print '\t'*self + '</%s>' % type
    def openclose(self, type, **kwargs):
        self.open(type, **kwargs)
        self.close(type)

def is_valid_type(t):
    '''used to check if a cursor has a type'''
    return t.kind != clang.cindex.TypeKind.INVALID

def qualifiers(t):
    '''set of qualifiers of a type'''
    q = set()
    if t.is_const_qualified(): q.add('const')
    if t.is_volatile_qualified(): q.add('volatile')
    if t.is_restrict_qualified(): q.add('restrict')
    return q

def show_type(t, level, title):
    '''pretty print type AST'''
    level.show(title, retrieve_type(t))

def is_definition(cursor):
    ''' Returns true if the cursor is the definition '''
    return (
        (cursor.is_definition() and not cursor.kind in (
            clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL,
            clang.cindex.CursorKind.TEMPLATE_TYPE_PARAMETER,
            clang.cindex.CursorKind.UNEXPOSED_DECL,
            )) or
        cursor.kind in (
            clang.cindex.CursorKind.FUNCTION_DECL,
            clang.cindex.CursorKind.CXX_METHOD,
            clang.cindex.CursorKind.FUNCTION_TEMPLATE,
            ))

def is_named_scope(cursor):
    ''' Returns true if the cursor is a name declaration   '''
    return cursor.kind in (
        clang.cindex.CursorKind.NAMESPACE,
        clang.cindex.CursorKind.STRUCT_DECL,
        clang.cindex.CursorKind.UNION_DECL,
        clang.cindex.CursorKind.ENUM_DECL,
        clang.cindex.CursorKind.CLASS_DECL,
        clang.cindex.CursorKind.CLASS_TEMPLATE,
        clang.cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
        )

def semantic_parents(cursor):
    import collections

    p = collections.deque()
    c = cursor.semantic_parent
    while c and is_named_scope(c):
        p.appendleft(c.displayname)
        c = c.semantic_parent
    return list(p)

def retrieve_type(t):
    '''retrieve actual type'''
    if is_valid_type(t.get_pointee()):
        pointee = ""
        if t.kind == clang.cindex.TypeKind.POINTER:
            pointee = "*"
        if t.kind == clang.cindex.TypeKind.LVALUEREFERENCE:
            pointee = "&"
        if t.kind == clang.cindex.TypeKind.RVALUEREFERENCE:
            pointee = "&&"
        return retrieve_type(t.get_pointee()) + pointee + ' '.join(qualifiers(t))
    else:
        ## GEe and decode TEMPLATE_TYPE_PARAMETER
        ## put together cursor.displayname (FOO) and cursor.type.get_canonical().spelling (type-paramter-0-0)
        ## for TYPEDEF_DECL remember cc[3].type.get_canonical().spelling (typename type-parameter-0-1::value_type)
        cursor = t.get_declaration()
        parents = semantic_parents(cursor)
        if cursor.displayname != "":
            return ' '.join(qualifiers(t)) + " " + "::".join(parents + [cursor.displayname])
        else:
            if getTypeFromCursor(t) == 'UNEXPOSED':
                return t.spelling
            return ' '.join(qualifiers(t)) + " " + "::".join(parents + [mangle_type(str(t.kind).split(".")[-1])])

authorized_decl = [
    "CXX_ACCESS_SPEC_DECL",
    "CXX_METHOD",
    "CXX_BASE_SPECIFIER",
    "CLASS_DECL",
    "CLASS_TEMPLATE",
    "CLASS_TEMPLATE_PARTIAL_SPECIALIZATION",
    "CLASS_DECL",
    "ENUM_DECL",
    "CONSTRUCTOR",
    "DESTRUCTOR",
    "FIELD_DECL",
    "FUNCTION_DECL",
    "FUNCTION_TEMPLATE",
    "TYPE_ALIAS_DECL",
    "TYPEDEF_DECL",
    "NAMESPACE",
    "STRUCT_DECL",
    "TRANSLATION_UNIT",
    "UNION_DECL",
    ]

printable_types = {
    "BOOL" : "bool",
    "CHAR" : "char",
    "CHAR_S" : "char",
    "DOUBLE" : "double",
    "FLOAT" : "float",
    "INT" : "int",
    "LONG" : "long",
    "LONGDOUBLE" : "long double",
    "LONGLONG" : "long long",
    "SCHAR" : "char",
    "UINT" : "unsigned int",
    "ULONG" : "unsigned long",
    "USHORT" : "unsigned short",
    "VOID" : "void",
    }

def mangle_type(type):
    return printable_types.get(type, type)

def show_ast(cursor, filter_pred=verbose, level=Level(), inherited_attributes={}):
    '''pretty print cursor AST'''
    if filter_pred(cursor, level):
        type = str(cursor.kind).split(".")[-1]
        level1 = level+1
#        if type not in authorized_decl:
#            return
        if type == "CXX_ACCESS_SPEC_DECL":
            config = clang.cindex.Config()
            inherited_attributes["access"] = access_specifiers[config.lib.clang_getCXXAccessSpecifier(cursor)]
            return
        # if type == "CLASS_DECL":
        #     level = ClassLevel()
        #     level1 = level+1
        level.open(type, spelling=cursor.spelling, displayname=cursor.displayname, location=cursor.location, **inherited_attributes)
        if is_valid_type(cursor.type):
            level1.openclose("type", displayname=retrieve_type(cursor.type.get_canonical()), location=cursor.location)
        attributes = {}
        if type == "CLASS_DECL":
            attributes["access"] = "private"
        elif type == "STRUCT_DECL":
            attributes["access"] = "public"
        if type == "CXX_METHOD" or type == "FUNCTION_DECL":
            level1.openclose("result", displayname=retrieve_type(cursor.result_type), location=cursor.location)
            for i, arg in enumerate(cursor.get_arguments()):
              level1.openclose("arg%i" %i, displayname=retrieve_type(arg.type), name=arg.displayname, location=arg.location)
        else:
            for c in cursor.get_children():
                show_ast(c, filter_pred, level1, attributes)
        level.close(type)

def getTypeFromCursor(cursor):
        return str(cursor.kind).split(".")[-1]

def computeBaseClass(cursor):
    for c in cursor.get_children():
        if getTypeFromCursor(c) == 'CXX_BASE_SPECIFIER':
            return retrieve_type(c.type.get_canonical()).replace('<', '__').replace('>', '__')
    return None

def getEnumConstants(cursor):
    enum = {}
    enum['name'] = retrieve_type(cursor.type.get_canonical()).lstrip()
    enum['values'] = []
    for c in cursor.get_children():
        enum['values'].append(c.displayname.lstrip())
    return enum

def getTypedef(cursor):
    typedef = {}
    typedef['old'] = retrieve_type(cursor.type.get_canonical()).lstrip()
    typedef['alias'] = cursor.displayname.lstrip()
    return typedef

def getTemplateParameters(cursor, a_class):
    for c in cursor.get_children():
        if getTypeFromCursor(c) == 'TEMPLATE_TYPE_PARAMETER':
            a_class.setdefault('%s' % c.type.get_canonical().spelling, c.displayname)

def analyseClass(cursor, a_class, access, indent=""):
    type = getTypeFromCursor(cursor)
    config = clang.cindex.Config()
    variable_type = 'int'
    if type not in authorized_decl:
        return
    if type == "CLASS_TEMPLATE":
        getTemplateParameters(cursor, a_class)
    if type in ["CLASS_DECL", "CLASS_TEMPLATE"]:
        base_class = computeBaseClass(cursor)
        a_nested_class = {}
        a_nested_class['classname'] = a_class['classname'] + '::' + cursor.displayname
        a_nested_class['derived_from'] = base_class if base_class else ''
        for c in cursor.get_children():
            analyseClass(c, a_nested_class, access, indent=indent+"  ")
        a_class.setdefault('nested_classes', []).append(a_nested_class)
    else:
        if type == "CXX_ACCESS_SPEC_DECL":
            access = access_specifiers_UML[config.lib.clang_getCXXAccessSpecifier(cursor)]
        if type in ["CXX_METHOD", "FUNCTION_DECL", "CONSTRUCTOR", "DESTRUCTOR"]:
            result = retrieve_type(cursor.result_type)
            isVirtual = config.lib.clang_CXXMethod_isVirtual(cursor)
            isPureVirtual = config.lib.clang_CXXMethod_isPureVirtual(cursor)
            if isPureVirtual:
                a_class.setdefault('abstract', 'abstract')
            try:
                a_class.setdefault('methods',[]).append({'access': access, 'isVirtual': isVirtual, 'isPureVirtual': isPureVirtual, 'displayname': cursor.displayname, 'result': result})
            except:
                print "Failure"
        if is_valid_type(cursor.type):
            variable_type = retrieve_type(cursor.type.get_canonical())
        if type == "FIELD_DECL":
            try:
                a_class.setdefault('members',[]).append({'access': access, 'type': variable_type, 'displayname': cursor.displayname})
            except:
                print "Failure1"
        elif type == "STRUCT_DECL":
            access = "+"
        if type == "ENUM_DECL":
            a_class.setdefault('enums', []).append(getEnumConstants(cursor))
        if type in ["TYPEDEF_DECL", "TYPE_ALIAS_DECL"]:
            a_class.setdefault('typedefs', []).append(getTypedef(cursor))
        for c in cursor.get_children():
            analyseClass(c, a_class, access, indent=indent+"  ")

def look_ast_for_classes(cursor, classes, filter_pred=verbose, level=0):
    '''pretty print cursor AST'''
    if filter_pred(cursor, level):
        level = level + 1
        type = getTypeFromCursor(cursor)
        if type not in authorized_decl:
            return
        if type in ["CLASS_DECL", "CLASS_TEMPLATE"]:
            a_class = {}
            base_class = computeBaseClass(cursor)
            a_class['classname'] = cursor.displayname
            a_class['derived_from'] = base_class if base_class else ''
            for c in cursor.get_children():            
                analyseClass(c, a_class, "+", indent="  ")
            classes.append(a_class)
        else:
            for c in cursor.get_children():
                look_ast_for_classes(c, classes, no_system_includes, level)

def class_to_UML(a_class):
    # Avoid saving forward declared classes
    if not len(a_class.get('methods', [])) and not len(a_class.get('members', [])) and not len(a_class.get('enums', [])) and not len(a_class.get('typedefs', [])):
        return
    output_filename = ''
    if a_class['derived_from'] != '':
        output_filename = '%s::%s.uml' % (a_class['classname'], a_class['derived_from'].lstrip())
    else:
        output_filename = '%s.uml' % (a_class['classname'])
    f = open(output_filename, 'w')
    f.write('@startuml\n')
    if a_class['derived_from'] != '':
        f.write('%s --|> %s\n' % (a_class['classname'], a_class['derived_from']))
    f.write('%s class %s {\n' % (a_class.get('abstract', ''), a_class['classname']))
    f.write('-- methods --\n')
    for m in a_class.get('methods',[]):
        f.write('%s %s %s %s %s\n' % (m['access'],
                                      'virtual' if (m['isVirtual'] or m['isPureVirtual']) else '' ,
                                      m['result'], m['displayname'],
                                      ' = 0' if m['isPureVirtual'] else ''))
    f.write('-- members --\n')
    for m in a_class.get('members',[]):
        f.write('%s %s %s\n' % (m['access'], m['type'], m['displayname']))
    f.write('-- typedefs --\n')
    for m in a_class.get('typedefs',[]):
        mm = re.match('.*(type-parameter-\d+-\d+)', m['old'])
        if mm:
            m['old'] = m['old'].replace(mm.group(1), a_class['%s' % mm.group(1)])
        f.write('typedef %s %s\n' % (m['old'], m['alias']))
    f.write('}\n')
    for nested in a_class.get('nested_classes', []):
        class_to_UML(nested)
    for e in a_class.get('enums',[]):
        f.write('enum %s {\n' % (e['name']))
        for v in e['values']:
            f.write('%s\n' % v)
        f.write('}\n')
    f.write('@enduml\n')
    f.close()
    
if __name__ == '__main__':
    index = clang.cindex.Index.create()
    tu = index.parse(sys.argv[1], ["-xc++",
                                   "-I%s/src" % os.getenv('LOCALRT', ''),
                                   "-I%s/src" % os.getenv('CMSSW_RELEASE_BASE', ''),
                                   "-I%s/include" % os.getenv('SRT_ROOTSYS_SCRAMRTDEL', ''),
                                   "-I%s/include" % os.getenv('CLHEP_PARAM_PATH', ''),
                                   "-std=c++11"
                                   ])
#    print "Generating class UML for %s" % sys.argv[2]
    classes = []
    look_ast_for_classes(tu.cursor, classes, filter_pred=no_system_includes)
    for c in classes:
        if match(sys.argv[2], c['classname']):
            class_to_UML(c)
    if False:
        show_ast(tu.cursor, no_system_includes)
