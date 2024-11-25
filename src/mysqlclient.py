import pymysql
import opentelemetry.trace

tracer = opentelemetry.trace.get_tracer(__name__)


def database_exists(server, port, db_name, user, password):
    conn = pymysql.connect(
        host=server,
        port=int(port),
        user=user,
        password=password)

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
            result = cursor.fetchone()

    return result is not None


def create_schema(server, port, user, password,schema_file):
    conn = pymysql.connect(
        host=server,
        port=int(port),
        user=user,
        password=password)
    
    with open(schema_file) as fd:
        stmts = fd.read().split(';')
        for query in stmts:
            q = query.replace('\n', '')
            with conn.cursor() as cursor:
                cursor.execute(q)
                result = cursor.fetchone()
        conn.commit()
                

class MySQLClient:
    def __init__(self, server, port, db_name, user, password):
        self.mysqlserver = server
        self.mysqlport = port
        self.db = db_name
        self.password = password
        self.user = user

        self.connection = None
        self.cursor = None

    def setConnection(self):
        """
        """
        conn = pymysql.connect(
            host=self.mysqlserver,
            port=int(
                self.mysqlport),
            user=self.user,
            password=self.password,
            db=self.db)

        self.connection = conn

    @tracer.start_as_current_span('mysql_query')
    def executeQuery(self, query):
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        return results

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def closeConnection(self):
        if self.connection:
            self.connection.close()
            self.connection = None
