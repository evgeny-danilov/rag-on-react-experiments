import os
import pdb

from neo4j import GraphDatabase
from typing import Optional


class NeoClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.environ['NEO_DATABASE_URL'], auth=(os.environ['NEO_USER'], os.environ['NEO_PASSWORD'])
        )

    def query(self, query: str, params: Optional[dict] = None):
        with self.driver.session() as session:
            scope = session.run(query, params)
            # TODO: use `session.read_transaction` instead
            #  https://github.com/neo4j/NaLLM/blob/main/api/src/driver/neo4j.py#L85C47-L85C47

            return [item.data() for item in scope]
