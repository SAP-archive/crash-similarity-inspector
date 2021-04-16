from pymongo import MongoClient
from sqlalchemy import create_engine


class MongoConnection:
    """
    The life cycle management of MongoDB connection via context manager.
    Attributes:
        host: A host name.
        port: A port number.
        connection: Create a new MongoClient instance.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None

    def __enter__(self):
        self.connection = MongoClient(self.host, self.port)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


class SqlConnection:
    """
    Create a new Engine instance.
    """
    def __init__(self, uri):
        self.connection = create_engine(uri).connect()
