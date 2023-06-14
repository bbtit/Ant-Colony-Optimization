import psycopg2
import traceback
import pprint
import matplotlib.pyplot as plt

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

    parameter_id = 145
    bottleneck_list = []

    # 縦列→世代(昇順)・横行→各widthの割合を降順(100,90,80...0)
    counts = [[0]*11 for _ in range(100)]

    # 各世代のwidthの出現回数を取得
    for generation in range(0, 100):
        for bottleneck in range(0, 101, 10):
            # SQLクエリを実行
            cur.execute(f"""SELECT Count(ants.routebottleneck)
                        FROM ants
                        JOIN generations ON ants.generationid = generations.generationid
                        JOIN simulations ON generations.simulationid = simulations.simulationid
                        WHERE simulations.parameterid = {parameter_id} AND generations.generation_count = {generation} AND ants.routebottleneck = {bottleneck};""")

            # 結果を取得
            rows = cur.fetchall()

            # routenodesidの値をリストとして取得
            bottleneck_list.append([row[-1] for row in rows])

    for generation, row in enumerate(bottleneck_list):
        for width in row:
            counts[generation][10 - width // 10] += 1

    # 横行のwidthの出現回数の総和
    totals = [sum(width_count) for width_count in counts]

    # 縦列が探索回数・横行がその探索回数におけるwidthの割合
    ratios = [[count * 100 / total for count in row] for row, total in zip(counts, totals)]
    proportions = [[val * 100 / total for val in row] for total, row in zip(totals, counts)]
    transpose = list(map(list, (zip(*proportions))))

    # ! 最終的に欲しい二次元配列は縦軸→世代数、横軸→各widthの割合を降順(100→90→80...)

    # 表示するラベルの用意(世代数分)
    labels = list(range(len(counts)))

    # 棒グラフの棒のカラー
    color = ['#4F71BE','#DE8344','#A5A5A5','#F1C242','#6A99D0','#7EAB54','#2D4374','#934D21','#636363','#937424','#355D8D']
    bottom = [0] * len(labels)
    color_count = 0

    for row in transpose:
        plt.bar(labels, row, width=1.0, bottom=bottom, color=color[color_count])
        bottom = [sum(x) for x in zip(bottom, row)]
        color_count += 1


    # グラフの設定
    plt.ylim((0, 100))
    plt.xlabel('Search Count')
    plt.ylabel('Percentage')
    plt.savefig("log.SVG")
    plt.show()
    
    
    
    
    # # リストを出力
    print(*bottleneck_list,sep="\n")
    # print(len(bottleneck_list))
    # print(rows)
    pprint.pprint(counts)

except Exception as e:
    print(e)
    conn.rollback()
    print(traceback.format_exc())

finally:
    # カーソルと接続を閉じる
    cur.close()
    conn.close()
