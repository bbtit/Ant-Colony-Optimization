import psycopg2
import traceback

try:
    # データベースに接続
    conn = psycopg2.connect(
        dbname="simulation",
        user="asaken_n40",
        password="asaken_N40",
        host="localhost",
        port="5432"
    )
    # カーソルを作成
    cur = conn.cursor()

    # cur.execute(f"""SELECT Count(interests.routebottleneck)
    #                 FROM interests
    #                 JOIN generations ON interests.generationid = generations.generationid
    #                 JOIN simulations ON generations.simulationid = simulations.simulationid
    #                 WHERE simulations.parameterid = 482
    #                 AND generations.generation_count = 5
    #                 AND interests.routebottleneck = 100;""")
    cur.execute(f"""SELECT *
                    FROM interests
                    JOIN generations ON interests.generationid = generations.generationid
                    JOIN simulations ON generations.simulationid = simulations.simulationid
                    WHERE simulations.parameterid = 482
                    AND generations.generation_count = 5
                    AND interests.routebottleneck = 100;""")

    rows = cur.fetchall()

    print(rows[0][0])


except Exception as e:
    print(e)
    conn.rollback()
    print(traceback.format_exc())

finally:
    cur.close()
    conn.close()