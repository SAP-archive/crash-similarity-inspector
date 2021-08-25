import configparser
import os
import re

from clang.cindex import Config
from clang.cindex import Index
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
        Obtain the paths of header file in current directory.
        Args:
            dir_path: The dictionary to be processed.
        Returns:
            The paths of header file.
        """
        headers = []
        stack = [dir_path]
        # DFS
        while stack:
            prefix = stack.pop()
            for node in os.listdir(prefix):
                curr_path = os.path.join(prefix, node)
                if os.path.isdir(curr_path):
                    stack.append(curr_path)
                    continue
                if os.path.splitext(curr_path)[-1] in [".h", ".hpp"]:
                    headers.append(curr_path)
        return headers

    def fully_qualified(self, node, path):
        """
        Obtain fully qualified name recursively.
        Args:
            node: A node in abstract syntax tree.
            path: The path of current header file.
        Returns:
            The fully qualified name that belongs to current node.
        """
        if node.location.file is None:
            return ""
        elif node.location.file.name != path:
            return ""
        else:
            ret = self.fully_qualified(node.semantic_parent, path)
            if ret != "":
                return ret + "::" + node.spelling
        return node.spelling

    def find_function(self, path):
        """
        Obtain all fully qualified names from current header file.
        Args:
            path: The path of current header file.
        Returns:
            All fully qualified names in the header file.
        """
        # remove it when include dependencies resolved
        git_root = "hana"
        header = os.path.join(git_root, "rte", "rtebase", "include")
        arguments = ["-x", "c++", "-I" + git_root, "-I" + header]
        index = Index.create()
        tu = index.parse(path, arguments)
        func_dict = dict()
        decl_kinds = {
            "FUNCTION_DECL", "CXX_METHOD",
            "CONSTRUCTOR", "DESTRUCTOR", "CONVERSION_FUNCTION"
        }
        cpnt = Component().best_matched(path)
        for node in tu.cursor.walk_preorder():
            if node.location.file and node.location.file.name == path and node.spelling:
                if str(node.kind).split(".")[1] in decl_kinds:
                    func = self.fully_qualified(node, path)
                    func_dict[func] = cpnt
        return func_dict

    def multi_process(self, paths):
        """
        Use multi-process to parse functions in the header file.
        Args:
            paths: All header files' paths in code base.
        Returns:
            The function parsing result from code base.
        """
        # using multi-process
        pool = Pool(os.cpu_count())
        functions = pool.imap(self.find_function, paths)
        pool.close(), pool.join()
        ret = dict()
        for func_dict in [i for i in functions if i]:
            for func in func_dict:
                k = func
                # handle anonymous namespace
                while "::::" in k:
                    k = k.replace("::::", "::")
                # remove special characters
                if re.search(r"[^\w:~]", k):
                    idx = re.search(r"[^\w:~]", k).span()[0]
                    k = k[:idx]
                ret[k] = func_dict[func]
        return ret

    def update_function(self):
        """
        Obtain File-Function mapping through Python bindings for Clang and load into database.
        """
        # load libclang.so
        if not Config.loaded:
            Config.set_library_path("/usr/local/lib")
        git_root = "hana"
        function_map = dict()
        for node in os.listdir(git_root):
            curr_path = os.path.join(git_root, node)
            if os.path.isdir(curr_path):
                print(curr_path)
                # update functions by directory
                headers = self.header_path(curr_path)
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
        print(f"\x1b[32mSuccessfully updated File-Function mapping ({len(documents)}).\x1b[0m")

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
