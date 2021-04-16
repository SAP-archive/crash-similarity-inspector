import configparser
import glob
import os
import re
import subprocess

from pool import MongoConnection


class Component:
    """
    Obtain Component-File mapping based on the layered CMakeLists.txt.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # MongoDB
    host = config.get("mongodb", "host")
    port = config.getint("mongodb", "port")
    # Git
    git_url = config.get("git", "url")

    @staticmethod
    def find_component(path):
        """
        Obtain parent/child components from a CMakeLists.txt path.
        Args:
            path: A CMakeLists.txt path.
        Returns:
            Parent and its children.
        """
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
        parent_pattern = re.compile(r'SET_COMPONENT\("(.+)"\)', re.M)
        child_pattern = re.compile(r'SET_COMPONENT\("(.+)"\n([^)]+)\)', re.M)
        parent = parent_pattern.findall(content)
        children = child_pattern.findall(content)
        return parent + children

    @staticmethod
    def convert_path(components, prefix):
        """
        Obtain the file path for corresponding component.
        Args:
            components: Parent component or child component list.
            prefix: The current prefix of CMakeLists.txt.
        Returns:
            Component-File mapping.
        """
        result = dict()
        for cpnt in components:
            # convert child component
            if isinstance(cpnt, tuple):
                for item in [i.strip() for i in cpnt[1].split("\n") if i.strip()]:
                    path = prefix
                    for layer in item.split("/"):
                        path = os.path.join(path, layer)
                    # wild character
                    for wild in glob.iglob(path):
                        result[wild] = cpnt[0]
                continue
            # convert parent component
            if isinstance(cpnt, str):
                result[prefix] = cpnt
        return result

    def update_component(self):
        """
        Obtain Component-File mapping based on the layered CMakeLists.txt and load into database.
        """
        git_root = "hana"
        # update source code base
        if os.path.exists(git_root):
            print("Removing from '{}'...".format(git_root))
            cmd = "rm -fr {}".format(git_root)
            subprocess.call(cmd.split(" "))
            print("\x1b[32mSuccessfully removed code base.\x1b[0m")
        cmd = "git clone --branch master --depth 1 {} {}".format(self.git_url, git_root)
        subprocess.call(cmd.split(" "))
        component_map = dict()
        queue = [git_root]
        # BFS
        while len(queue) > 0:
            prefix = queue.pop(0)
            cmk_path = os.path.join(prefix, "CMakeLists.txt")
            if os.path.exists(cmk_path):
                components = self.find_component(cmk_path)
                component_map.update(self.convert_path(components, prefix))
            for node in os.listdir(prefix):
                item = os.path.join(prefix, node)
                if os.path.isdir(item):
                    queue.append(item)
        # insert documents
        documents = []
        for key in sorted(component_map.keys()):
            data = dict()
            data["path"] = key
            data["component"] = component_map[key]
            documents.append(data)
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["component"]
            collection.drop()
            collection.insert_many(documents)
        print("\x1b[32mSuccessfully updated Component-File mapping ({}).\x1b[0m".format(len(documents)))

    def best_matched(self, path):
        """
        Query the component collection to obtain the best matched component.
        Args:
            path: A absolute path is the stack frame.
        Returns:
            matched: The best matched component.
        """
        matched = "UNKNOWN"
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["component"]
            data = collection.find_one({"path": path})
            if not data:
                while "/" in path:
                    path = path[:path.rindex("/")]
                    data = collection.find_one({"path": path})
                    if data:
                        matched = data["component"]
                        break
            else:
                matched = data["component"]
        return matched
