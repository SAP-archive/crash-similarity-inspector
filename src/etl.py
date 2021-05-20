import configparser
import hashlib
import os
import requests

from component import Component
from datetime import datetime
from knowledge import Knowledge
from pool import MongoConnection, SqlConnection
from process import Process


class ETL:
    """
    The Extract, Transform, Load process for data crawling.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # MongoDB
    host = config.get("mongodb", "host")
    port = config.getint("mongodb", "port")
    # SQL
    qdb_uri = config.get("sql", "qdb_uri")
    cdb_uri = config.get("sql", "cdb_uri")
    # ETL
    months = config.getint("etl", "months")

    def extract_qdb(self):
        """
        Extract recent data from database.
        Returns:
            test_id, start_time, dump_link, bug_id.
        """
        set_schema = """SET SCHEMA TESTER;"""
        extract_content = """
        SELECT TEST_MANY.ID, TEST_MANY.START_TIME, TEST_MANY.LINK, TEST_MANY.BUG_ID
        FROM
            (
                SELECT TEST_CASES.ID, TEST_CASES.START_TIME, TEST_LOG_FILES.LINK, TEST_COMMENTS.BUG_ID
                FROM TEST_CASES
                    JOIN TEST_LOG_FILES ON TEST_CASES.ID = TEST_LOG_FILES.ID_TEST_CASE
                    JOIN
                    (
                        SELECT ID_TEST_CASE, MAX(ID_COMMENT) AS ID
                        FROM TEST_REVIEW
                        WHERE TEST_CASE_CLASSIFICATION = 'known'
                        GROUP BY ID_TEST_CASE
                    ) AS TEST_VALID
                    ON TEST_CASES.ID = TEST_VALID.ID_TEST_CASE
                    JOIN TEST_COMMENTS ON TEST_VALID.ID = TEST_COMMENTS.ID
                    JOIN TEST_PROFILES ON TEST_CASES.ID_TEST_PROFILE = TEST_PROFILES.ID
                    JOIN MAKES ON TEST_PROFILES.ID_MAKE = MAKES.ID
                WHERE TEST_CASES.START_TIME >= ADD_MONTHS(TO_DATE(CURRENT_DATE), -{})
                    AND TEST_LOG_FILES.DUMP_TYPE = 'CRASH'
                    AND TEST_LOG_FILES.LINK NOT LIKE '%recursive.trc%'
                    AND TEST_COMMENTS.BUG_ID != 0
                    AND MAKES.BUILD_PURPOSE = 'G'
                    AND (MAKES.COMPONENT = 'HANA' OR MAKES.COMPONENT = 'Engine')
            ) AS TEST_MANY
            JOIN
            (
                SELECT TEST_CASES.ID, COUNT(TEST_LOG_FILES.LINK) AS NUM
                FROM TEST_CASES
                    JOIN TEST_LOG_FILES ON TEST_CASES.ID = TEST_LOG_FILES.ID_TEST_CASE
                    JOIN
                    (
                        SELECT ID_TEST_CASE, MAX(ID_COMMENT) AS ID
                        FROM TEST_REVIEW
                        WHERE TEST_CASE_CLASSIFICATION = 'known'
                        GROUP BY ID_TEST_CASE
                    ) AS TEST_VALID
                    ON TEST_CASES.ID = TEST_VALID.ID_TEST_CASE
                    JOIN TEST_COMMENTS ON TEST_VALID.ID = TEST_COMMENTS.ID
                    JOIN TEST_PROFILES ON TEST_CASES.ID_TEST_PROFILE = TEST_PROFILES.ID
                    JOIN MAKES ON TEST_PROFILES.ID_MAKE = MAKES.ID
                WHERE TEST_CASES.START_TIME >= ADD_MONTHS(TO_DATE(CURRENT_DATE), -{})
                    AND TEST_LOG_FILES.DUMP_TYPE = 'CRASH'
                    AND TEST_COMMENTS.BUG_ID != 0
                    AND MAKES.BUILD_PURPOSE = 'G'
                    AND (MAKES.COMPONENT = 'HANA' OR MAKES.COMPONENT = 'Engine')
                GROUP BY TEST_CASES.ID
            ) AS TEST_ONLY
            ON TEST_MANY.ID = TEST_ONLY.ID
        WHERE TEST_ONLY.NUM = 1
        ORDER BY TEST_MANY.START_TIME DESC;
        """.format(self.months, self.months)
        with SqlConnection(self.qdb_uri).connection as sql:
            sql.execute(set_schema)
            result = sql.execute(extract_content).fetchall()
        return result

    def extract_cdb(self, test_id):
        """
        Extract history data from database via test_id.
        Returns:
            callstack_string.
        """
        extract_content = """
        SELECT HANAQA.CRASHES.CALLSTACK_STRING
        FROM HANAQA.QADB_CRASHES
            JOIN HANAQA.CRASHES
            ON HANAQA.QADB_CRASHES.CRASH_ID = HANAQA.CRASHES.CRASH_ID
        WHERE HANAQA.QADB_CRASHES.TEST_CASE_ID = {}
        UNION ALL
        SELECT BUGZILLA.CRASHES.CALLSTACK_STRING
        FROM HANAQA.QADB_CRASHES
            JOIN BUGZILLA.CRASHES
            ON HANAQA.QADB_CRASHES.CRASH_ID = BUGZILLA.CRASHES.CRASH_ID
        WHERE HANAQA.QADB_CRASHES.TEST_CASE_ID = {};
        """.format(test_id, test_id)
        with SqlConnection(self.cdb_uri).connection as sql:
            result = sql.execute(extract_content).fetchall()
        return result[0][0]

    def extract_word(self):
        """
        Extract stop words from database.
        Returns:
            test_id, dump_link.
        """
        set_schema = """SET SCHEMA TESTER;"""
        extract_content = """
        SELECT TEST_MANY.ID
        FROM
            (
                SELECT TEST_CASES.ID, TEST_CASES.START_TIME, TEST_LOG_FILES.LINK
                FROM TEST_CASES
                    JOIN TEST_LOG_FILES ON TEST_CASES.ID = TEST_LOG_FILES.ID_TEST_CASE
                    JOIN TEST_REVIEW ON TEST_CASES.ID = TEST_REVIEW.ID_TEST_CASE
                    JOIN TEST_PROFILES ON TEST_CASES.ID_TEST_PROFILE = TEST_PROFILES.ID
                    JOIN MAKES ON TEST_PROFILES.ID_MAKE = MAKES.ID
                WHERE TEST_CASES.START_TIME >= ADD_MONTHS(TO_DATE(CURRENT_DATE), -{})
                    AND TEST_LOG_FILES.DUMP_TYPE = 'CRASH'
                    AND TEST_LOG_FILES.LINK NOT LIKE '%recursive.trc%'
                    AND MAKES.BUILD_PURPOSE = 'G'
                    AND (MAKES.COMPONENT = 'HANA' OR MAKES.COMPONENT = 'Engine')
            ) AS TEST_MANY
            JOIN
            (
                SELECT TEST_CASES.ID, COUNT(TEST_LOG_FILES.LINK) AS NUM
                FROM TEST_CASES
                    JOIN TEST_LOG_FILES ON TEST_CASES.ID = TEST_LOG_FILES.ID_TEST_CASE
                    JOIN TEST_REVIEW ON TEST_CASES.ID = TEST_REVIEW.ID_TEST_CASE
                    JOIN TEST_PROFILES ON TEST_CASES.ID_TEST_PROFILE = TEST_PROFILES.ID
                    JOIN MAKES ON TEST_PROFILES.ID_MAKE = MAKES.ID
                WHERE TEST_CASES.START_TIME >= ADD_MONTHS(TO_DATE(CURRENT_DATE), -{})
                    AND TEST_LOG_FILES.DUMP_TYPE = 'CRASH'
                    AND MAKES.BUILD_PURPOSE = 'G'
                    AND (MAKES.COMPONENT = 'HANA' OR MAKES.COMPONENT = 'Engine')
                GROUP BY TEST_CASES.ID
            ) AS TEST_ONLY
            ON TEST_MANY.ID = TEST_ONLY.ID
        WHERE TEST_ONLY.NUM = 1
        ORDER BY TEST_MANY.START_TIME DESC;
        """.format(self.months, self.months)
        with SqlConnection(self.qdb_uri).connection as sql:
            sql.execute(set_schema)
            result = sql.execute(extract_content).fetchall()
        return result

    def transform(self):
        """
        Convert original crash dump information into the target data format.
        Returns:
            Documents to be stored.
        """
        documents = []
        hash_value = set()
        result = self.extract_qdb()
        count, total = 0, len(result)
        for row in result:
            count += 1
            test_id, time_stamp, url, bug_id = row
            print("{}, {}/{}".format(test_id, count, total))
            try:
                if requests.get(url, verify=False).status_code == 200:
                    dump = requests.get(url, verify=False).content.decode("utf-8")
                    processed = Process(dump).pre_process()
                else:
                    dump = self.extract_cdb(test_id)
                    processed = Process(dump).internal_process()
            except (IndexError, UnicodeDecodeError):
                continue
            cpnt_order, func_block = Knowledge(processed).add_knowledge()
            if not cpnt_order or not func_block:
                continue
            data = dict()
            data["test_id"] = test_id
            data["time_stamp"] = int(datetime.timestamp(time_stamp))
            data["cpnt_order"] = cpnt_order
            data["func_block"] = func_block
            data["bug_id"] = bug_id
            data["md5sum"] = hashlib.md5("".join("".join(i) for i in func_block).encode("utf-8")).hexdigest()
            # deduplication via set
            if data["md5sum"] in hash_value:
                continue
            hash_value.add(data["md5sum"])
            documents.append(data)
        return documents

    def load(self):
        """
        Load many documents into the database.
        """
        # knowledge updating
        Component().update_component()
        print("Start ETL process...")
        documents = self.transform()
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["dataset"]
            collection.drop()
            collection.insert_many(documents)
        print("\x1b[32mSuccessfully executed ETL process ({}).\x1b[0m".format(len(documents)))
