
import os
import inspect
import sys
import imp
import re
from igraph import *
import pprint
import collections
import simplejson

__author__ = 'Nikhil Rupanawar'

user_paths = os.environ.get('PYTHONPATH').split(os.pathsep)

current_dir = ['.']
priority_dir = []


module_path_cache = {}

def remove_comments(string):
    pattern = r"(\".*?\"|\'.*?\')|(\"\"\".*?\"\"\"|'''.*?'''|#[^\r\n]*$)"
    regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
    def _replacer(match):
        if match.group(2) is not None:
            return "" # so we will return empty to remove the comment
        else: # otherwise, we will return the 1st group
            return match.group(1) # captured quoted-string
    return regex.sub(_replacer, string)


def locate_module_file(module_name):
    
    if module_name in sys.builtin_module_names:
        return (module_name, 'builtin')

    if module_name in module_path_cache:
        return module_path_cache.get(module_name)

    all_paths = priority_dir + current_dir + sys.path + user_paths
    sub_module_path = module_name.split('.')
    if len(sub_module_path) > 1:
        sub_module_path = os.sep.join(sub_module_path)
    else:
        sub_module_path = sub_module_path[0]

    sub_module_path_file = sub_module_path + '.py'
    sub_module_path_file_pyc = sub_module_path + '.pyc'

    for path in all_paths:
        full_path_source = os.path.join(path, sub_module_path + '.py')
        full_path_pyc = os.path.join(path, sub_module_path + 'pyc')

        if os.path.isfile(full_path_source):
            module_path_cache[module_name] = (full_path_source, 'module')
            return (full_path_source, 'module')
        elif os.path.isfile(full_path_pyc):
            module_path_cache[module_name] = (full_path_pyc, 'module')
            return (full_path_pyc, 'module')
        # check if package
        full_path_dir = os.path.join(path, sub_module_path)
        if os.path.isdir(full_path_dir):
            module_path_cache[module_name] = (full_path_dir, 'package')
            init_file = os.path.join(full_path_dir, '__init__.py')
            if os.path.isfile(init_file):
                return (full_path_dir, 'package')

    return None, None


def locate_module_and_class(l, index=-1):
    global fullname

    newlist = l[:index]

    if not newlist:
        return (None, None, None, None)

    name = '.'.join(newlist)

    print name

    if not name or name == '.':
        return (None, None, None, None)

    module_path, mode = locate_module_file(name)

    if not module_path:
        newindex = index -1
        return locate_module_and_class(l, index=newindex)
    splitter = name + '.'
    rest = fullname.split(splitter)[-1]
    return (module_path, mode, name, rest)


def load_module_from_source_file(entry):
    with open(entry, 'U') as f:
        name = entry.split(os.sep)[-1].split('.py')[0]
        mod = imp.load_module(name, f, entry, ('.py', 'U', imp.PY_SOURCE))
        return mod

def load_module_from_bytecode_file(entry):
    with open(entry, 'U') as f:
        name = entry.split(os.sep)[-1].split('.pyc')[0]
        mod = imp.load_module(name, f, entry, ('.pyc', 'U', imp.PY_COMPILED))
        return mod

def load_package(entry):
    name = entry.split(os.sep)[-1]
    mod = imp.load_module(name, None, entry, ('', '', imp.PKG_DIRECTORY))
    return mod

def getimports(entry, caller):
    import_list = []
    
    data = None

    with open(entry) as f:
        data = f.read()

    data = remove_comments(data)
    lines = (l for l in data.split('\n'))
 
    for line in lines:
        m = re.match('(.*?)from[\s+](.*)[\s+]import[\s+](.*)', line)
        if m:
            import_dict = dict()
            import_dict['module_name'] = m.group(2)
            import_dict['imported_symbols'] =  m.group(3).split(',')
            import_dict['source'] = locate_module_file(m.group(2))
            import_list.append(import_dict)
        else:
            m = re.match('[\s+]?import[\s+](.*)', line)
            if m:
                l = m.group(1).split(',')
                for im in l: 
                     import_dict = dict()
                     import_dict['module_name'] = im
                     import_dict['source'] = locate_module_file(im)
                     import_list.append(import_dict)
    return import_list


def get_function(func, name=None):
    method_info = collections.OrderedDict()
    args = inspect.getargspec(func)
    if not name:
        name = str(func)
    method_info['name'] = str(name) 
    method_info['arguments'] = args.args
    method_info['doc'] = func.__doc__
    method_info['type'] = str(func.__class__)
    return method_info

def get_methods(_class):
   methods = []
   for name in _class.__dict__:

       try:
           item = getattr(_class, name, None)
           if not item: continue
           if inspect.ismethod(item):
               method_info = get_function(item, name)
               methods.append(method_info)
       except: pass

   return methods

def get_rest_class_attributes(_class):
   rest = []
   for name in _class.__dict__:
       try:
           item = getattr(_class, name)
           if not inspect.ismethod(item):
               attr_value = {name: str(item)}
               rest.append(attr_value)
       except: pass
   return rest

def get_info(mod, is_package=False):

    info = collections.OrderedDict()


    if str(type(mod)) != "<type 'module'>":
        
        if str(type(mod)) == "<type 'function'>":
            func_info = get_function(mod, mod.__name__)
            return func_info 

        if str(mod).startswith("<class"):
           _type = str(mod)
           _inheritance = inspect.getmro(mod)
           inheritance = []
           for t in _inheritance:
               inheritance.append(str(t))
           _methods = get_methods(mod)
           _class = collections.OrderedDict()
           _class['name'] = str(mod.__name__)
           _class['type'] = _type
           _class['inheritance'] = inheritance
           _class['methods'] = _methods
           _class['doc'] = mod.__doc__
           _class['attributes'] = get_rest_class_attributes(mod)
           return _class

       
        info['type'] = str(type(mod))
        info['value'] = str(mod) 
        return info

    members = inspect.getmembers(mod)
    classes = []
    methods = []
    global_functions = []
    global_variables = []
    modules = []
    info['package'] = mod.__package__
    info['doc'] = mod.__doc__
    info['type'] = str(type(mod))

    for name, data in members:
        if name == '__builtins__':
           continue

        elif inspect.isclass(data):

           if not data.__module__ == mod.__name__:
               continue

           _type = str(data)
           _inheritance = inspect.getmro(data)
           inheritance = []
           for t in _inheritance:
               inheritance.append(str(t))
           _methods = get_methods(data)
 
           _class = collections.OrderedDict()
           _class['name'] = str(name)
           _class['type'] = _type
           _class['inheritance'] = inheritance
           _class['methods'] = _methods
           _class['doc'] = data.__doc__
           _class['attributes'] = get_rest_class_attributes(mod)
           classes.append(_class)

        elif inspect.isfunction(data):
           if not data.__module__ == mod.__name__:
               continue
           func_info = get_function(data, name)
           global_functions.append(func_info)
           continue

        if is_package and name == '__all__':
           info['public_symbols'] = data
           continue

        global_variables.append([name, str(data)])

    info['classes'] = classes
    info['global_functions'] = global_functions
    info['misc_symbols'] = global_variables
    return info

def import_module(name):
    return __import__(name)

def load_module(module_path, mode):
    if mode == 'module':
       if module_path.endswith('.pyc'):
           return load_module_from_bytecode_file(module_path)
       return load_module_from_source_file(module_path)
    if mode == 'package':
       return load_package(module_path)
    if mode == 'builtin':
       return import_module(module_path)

def inspect_module_recursilvely(mod, rest, index=0):
    
    if index >= len(rest.split('.')):
         info = get_info(mod)
         return info

    current = rest.split('.')[index]

    members = inspect.getmembers(mod)
    for name, data in members:
        if name == current:
            mod = data
            index = index + 1
            return inspect_module_recursilvely(mod, rest, index=index) 
            
 
def explore(module):

   info = None

   if not module:
       raise Exception('No input given')
   elif os.path.isfile(module) and (module.endswith('.py') or module.endswith('.pyc')):
       mode = 'module'
       module_path = module
   else:
       module_path, mode = locate_module_file(module)

   if not module_path and '.' in module:
       global fullname
       fullname = module
       name = module
       l = name.split('.')
       module_path, mode, name, rest = locate_module_and_class(l, index=-1)

       if not module_path:
           raise Exception("Source or package not located not found for module [%s]." % module)
       print "Located module [source=%s, type of module=%s]" % (module_path, mode)
       print "Now resolve %s part"  % rest
       mod = load_module(module_path, mode)
       info = inspect_module_recursilvely(mod, rest)
       return info, mod

   if not module_path:
       raise Exception("Source or package not located not found for module [%s]." % module)

   print "Located module [source=%s, type of module=%s]" % (module_path, mode)

   mod = load_module(module_path, mode)

   if mode == 'module':
       info = get_info(mod)
       info['source_file'] = module_path
       if module_path.endswith('.py'):
           name = module_path.split(os.sep)[-1].split('.py')[0]
           info['imported_modules'] = getimports(module_path, name)
       elif module_path.endswith('.pyc'):
           name = module_path.split(os.sep)[-1].split('.pyc')[0]
       info['mode'] = 'module'

   elif mode == 'package':
       init_script = os.path.join(module_path, '__init__.py')
       name = module_path.split(os.sep)[-1]
       info = get_info(mod, True)
       info['source_file'] = init_script
       info['package_dir'] = module_path
       info['imported_modules'] = getimports(init_script, name)
       info['mode'] = 'package'

   elif mode == 'builtin':
       info = get_info(mod)
       info['mode'] = 'builtin_module'

   return info, mod

if __name__ == '__main__':

   if len(sys.argv) > 1 and sys.argv[1]: 
       input_string = sys.argv[1]
       info, mod = explore(input_string)
   else:
       while True:
           input_string = raw_input("Enter next module name to scan: ")
           if not module: continue
           info, mod = explore(input_string)
   
   print "================================"
   print "   Information "
   print "================================"
   print simplejson.dumps(info, indent=4, encoding="ISO-8859-1")
   print "================================="
   print "Finished module %s" % input_string
