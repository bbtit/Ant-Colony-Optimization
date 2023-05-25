import psycopg2
from psycopg2 import Error

# try:
#     #接続
#     connector =  psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format( 
#                 user="asaken_n40",        #ユーザ
#                 password="asaken_N40",  #パスワード
#                 host="localhost",       #ホスト名
#                 port="5432",            #ポート
#                 dbname="test"))    #データベース名
    
#     #カーソル取得
#     cursor = connector.cursor()
#     cursor.execute("INSERT INTO mytable VALUES (4, 'Nakagawa') RETURNING id;")
#     inserted_id = cursor.fetchone()[0]
#     print(inserted_id)
#     connector.commit()
    
# except(Exception, Error) as error:
#     print("PostgreSQLへの接続時のエラーが発生しました",error)

# #最後は必ずクローズ
# finally:
#     cursor.close()
#     connector.close()

    
class DBLogger:
    def __init__(self,user:str, password:str, host:str, db_name:str, port:str) -> None:
        self.connector = psycopg2.connect(f'postgresql://{user}:{password}@{host}:{port}/{db_name}')
        self.cursor = self.connector.cursor()
        self.user = user
        self.password = password
        self.host = host
        self.db_name = db_name
        self.port = port

    # 任意のクエリを実行し、結果を返さない
    def execute_query(self, query, params=None):
        self.cursor.execute(query, params)
        self.connector.commit()

    # 任意のクエリを実行し、結果を返す
    def fetch_result(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # INSERTクエリを実行し、生成されたIDを返す
    def insert_and_get_id(self, query, params=None):
        self.cursor.execute(query, params)
        self.connector.commit()
        self.cursor.execute("SELECT LASTVAL();")
        return self.cursor.fetchone()[0]
    
    # データベース接続を閉じる
    def close(self):
        self.cursor.close()
        self.connector.close()

dblogger = DBLogger("asaken_n40","asaken_N40","localhost","test","5432")
result = dblogger.fetch_result("SELECT * FROM mytable;")
print(result)
dblogger.close()