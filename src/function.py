import configparser
import os
import re

from clang.cindex import Index
from clang.cindex import Config
from collections import Counter
from component import Component
from multiprocessing import Pool
from pool import MongoConnection


class Function:
    """
    Obtain File-Function mapping through Python bindings for Clang.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # MongoDB
    host = config.get("mongodb", "host")
    port = config.getint("mongodb", "port")

    @staticmethod
    def header_path(dir_path):
        """
        Obtain all header file's paths in the current directory.
        Args:
            dir_path: The dictionary to be processed.
        Returns:
            All header file's paths in the directory.
        """
        headers = []
        stack = [dir_path]
        # DFS
        while len(stack) > 0:
            prefix = stack.pop()
            for node in os.listdir(prefix):
                cur_path = os.path.join(prefix, node)
                extension = os.path.splitext(cur_path)[-1]
                if not os.path.isdir(cur_path):
                    if extension in [".h", ".hpp"]:
                        headers.append(cur_path)
                else:
                    stack.append(cur_path)
        return headers

    def fully_qualified(self, node, path):
        """
        Obtain fully qualified name recursively.
        Args:
            node: A node in abstract syntax tree.
            path: The path of current header file.
        Returns:
            The fully qualified name that belongs to the node.
        """
        if node.location.file is None:
            return ""
        elif node.location.file.name != path:
            return ""
        else:
            result = self.fully_qualified(node.semantic_parent, path)
            if result != "":
                return result + "::" + node.spelling
        return node.spelling

    def find_function(self, path):
        """
        Obtain all fully qualified names from the current header file.
        Args:
            path: The path of current header file.
        Returns:
            All fully qualified names in the header file.
        """
        result = dict()
        index = Index.create()
        cpnt = Component().best_matched(path)
        # remove it when include dependencies resolved
        git_root = "hana"
        header = os.path.join(git_root, "rte", "rtebase", "include")
        arguments = ["-x", "c++", "-I" + git_root, "-I" + header]
        tu = index.parse(path, arguments)
        decl_kinds = [
            "FUNCTION_DECL",
            "CXX_METHOD",
            "CONSTRUCTOR",
            "DESTRUCTOR",
            "CONVERSION_FUNCTION"
        ]
        for node in tu.cursor.walk_preorder():
            if node.location.file is not None and node.location.file.name == path and node.spelling:
                kind = str(node.kind)[str(node.kind).index('.') + 1:]
                if kind in decl_kinds:
                    key = self.fully_qualified(node, path)
                    result[key] = cpnt
        return result

    def multi_process(self, paths):
        """
        Use multi-process to parse functions in the header file.
        Args:
            paths: All header file's paths in the code base.
        Returns:
            Function parsing result from the code base.
        """
        result = dict()
        # using multi-process
        pool = Pool(40)
        functions = pool.map(self.find_function, paths)
        pool.close()
        pool.join()
        for func in [i for i in functions if i]:
            for k in func.keys():
                key = k
                # handle anonymous namespace
                while "::::" in key:
                    key = key.replace("::::", "::")
                # remove special characters
                if re.search(r"[^0-9a-zA-Z:_~]", key):
                    point = re.search(r"[^0-9a-zA-Z:_~]", key).span()[0]
                    key = key[:point]
                result[key] = func[k]
        return result

    def update_function(self):
        """
        Obtain File-Function mapping through Python bindings for Clang and load into database.
        """
        # load libclang.so
        lib_path = "/usr/local/lib"
        if not Config.loaded:
            Config.set_library_path(lib_path)
        function_map = dict()
        git_root = "hana"
        for node in os.listdir(git_root):
            cur_path = os.path.join(git_root, node)
            if os.path.isdir(cur_path):
                print(cur_path)
                # update functions by directory
                headers = self.header_path(cur_path)
                if headers:
                    function_map.update(self.multi_process(headers))
        # insert documents
        documents = []
        for key in sorted(function_map.keys()):
            data = dict()
            data["function"] = key
            data["component"] = function_map[key]
            documents.append(data)
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["function"]
            collection.drop()
            collection.insert_many(documents)
        print("\x1b[32mSuccessfully updated File-Function mapping ({}).\x1b[0m".format(len(documents)))

    def best_matched(self, function):
        """
        Query the function collection to obtain the best matched component.
        Args:
            function: A demangled function is the stack frame.
        Returns:
            matched: The best matched component.
        """
        matched = "UNKNOWN"
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["function"]
            data = collection.find_one({"function": function})
            if not data:
                components = []
                while "::" in function:
                    function = function[:function.rindex("::")]
                    candidates = collection.find({"function": {"$regex": "^%s(:{2}|$)" % function}})
                    for cand in candidates:
                        components.append(cand["component"])
                    if components:
                        # handle equal numbers
                        stats = Counter(components).most_common()
                        if len(stats) > 1 and stats[1][1] == stats[0][1]:
                            matched = stats[1][0]
                        else:
                            matched = stats[0][0]
                        break
            else:
                matched = data["component"]
        return matched
