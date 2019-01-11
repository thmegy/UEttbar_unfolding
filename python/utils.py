#!/bin/env python
import hjson, json

class NumpyEncoder(json.JSONEncoder):
    """
    For converting numpy arrays into lists that can be written to JSON file
    """
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class MyJSONEncoder(json.JSONEncoder):
    """
    For pretty-printing JSON in a more human-readable form
    """
    def __init__(self, *args, **kwargs):
        super(MyJSONEncoder, self).__init__(*args, **kwargs)
        self.current_indent = 0
        self.current_indent_str = ""

    def encode(self, o):
        from numpy import ndarray
        #Special Processing for lists
        if isinstance(o, (list, tuple, ndarray)):
            primitives_only = True
            for item in o:
                if isinstance(item, (list, tuple, dict, ndarray)):
                    primitives_only = False
                    break
            output = []
            if primitives_only:
                for item in o:
                    output.append(json.dumps(item, cls=NumpyEncoder))
                return "[ " + ", ".join(output) + " ]"
            else:
                self.current_indent += self.indent
                self.current_indent_str = "".join( [ " " for x in range(self.current_indent) ])
                for item in o:
                    output.append(self.current_indent_str + self.encode(item))
                self.current_indent -= self.indent
                self.current_indent_str = "".join( [ " " for x in range(self.current_indent) ])
                return "[\n" + ",\n".join(output) + "\n" + self.current_indent_str + "]"
        elif isinstance(o, dict):
            output = []
            self.current_indent += self.indent
            self.current_indent_str = "".join( [ " " for x in range(self.current_indent) ])
            for key, value in o.items():
                output.append(self.current_indent_str + json.dumps(key, cls=NumpyEncoder) + ": " + self.encode(value))
            self.current_indent -= self.indent
            self.current_indent_str = "".join( [ " " for x in range(self.current_indent) ])
            return "{\n" + ",\n".join(output) + "\n" + self.current_indent_str + "}"
        else:
            return json.dumps(o, cls=NumpyEncoder)


def readjson(fname, is_hjson=False):
    if len(fname) < 5 or fname[-5:] != '.json':
        fname += '.json'
    if is_hjson:
        return hjson.load(open(fname, 'r'))
    else:
        return json.load(open(fname, 'r'))


def writejson(fname='',datatowrite=None):
    if len(fname) < 5 or fname[-5:] != '.json':
        fname += '.json'
    with open(fname,'w') as outfile:
        outfile.write(json.dumps(datatowrite, cls=MyJSONEncoder, indent=4))


