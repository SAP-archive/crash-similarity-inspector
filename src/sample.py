import bugzilla
import configparser
import os

from collections import defaultdict
from pool import MongoConnection
from itertools import combinations
from random import sample
from utils import UF


class Sample:
    """
    Sample negatives and positives via bug_id.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # MongoDB
    host = config.get("mongodb", "host")
    port = config.getint("mongodb", "port")
    # Bugzilla
    url = config.get("bugzilla", "url")
    key = config.get("bugzilla", "key")

    def bug_map(self):
        """
        Obtain the mapping relationship between bug_id and test_id.
        Returns:
            bug_map: The bug_id/test_id mapping.
        """
        bug_map = defaultdict(list)
        # obtain bug_id/test_id mapping
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["dataset"]
            dataset = collection.find()
        for data in dataset:
            bug_id, test_id = data["bug_id"], data["test_id"]
            bug_map[bug_id].append(test_id)
        return bug_map

    def union_map(self, bug_list):
        """
        Obtain the mapping relationship between bug_id and group_id.
        Args:
            bug_list: The key list of bug_map.
        Returns:
            union_map: The bug_id/group_id mapping.
        """
        pairs = []
        bzapi = bugzilla.Bugzilla(self.url, api_key=self.key, sslverify=False)
        # obtain bug_id/group_id mapping
        for bug_id in bug_list:
            bug = bzapi.getbug(bug_id)
            if bug.dupe_of and bug.dupe_of in bug_list:
                pairs.append([bug_id, bug.dupe_of])
        uf = UF(len(bug_list))
        for pair in pairs:
            uf.union(bug_list.index(pair[0]), bug_list.index(pair[1]))
        union_map = dict(zip(bug_list, uf.id))
        return union_map

    def group_data(self):
        """
        Group test_ids via group_id if the root cause is same.
        Returns:
            groups: The result of test_id grouping.
        """
        groups = []
        bug_map = self.bug_map()
        union_map = self.union_map(list(bug_map.keys()))
        # test_id grouping
        for union_id in set(union_map.values()):
            group = []
            for k, v in union_map.items():
                if v == union_id:
                    group.extend(bug_map[k])
            if len(group) > 1:
                groups.append(group)
        return groups

    def sample_data(self):
        """
        Sample data based on combination and random methods.
        Returns:
            The negatives and positives after sampling.
        """
        print("Start data sampling...")
        positives, negatives = [], []
        groups = self.group_data()
        for group in groups:
            positives.extend(list(combinations(group, 2)))
        for _ in range(len(positives)):
            group1, group2 = sample(groups, 2)
            negatives.append((sample(group1, 1)[0], sample(group2, 1)[0]))
        print("\x1b[32mSuccessfully completed data sampling ({} x 2).\x1b[0m".format(len(positives)))
        return [negatives, positives]
