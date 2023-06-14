
# ! 100%積み上げ棒グラフのために最終的に欲しい二次元配列は
# ! 縦軸→widthを降順(100→90→80...)、横軸→世代数(昇順)、要素→その世代におけるそのwidthの割合
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

    parameter_id = 482
    # 縦列→世代(昇順)、横行→widthを降順(100,90,80...0)、要素→その世代におけるそのwidthの回数
    width_counts_matrix = [[0]*11 for _ in range(100)]

    # 各世代のwidthの出現回数を取得
    for generation in range(0, 100):
        for bottleneck in range(0, 101, 10):
            # SQLクエリを実行
            cur.execute(f"""SELECT Count(interests.routebottleneck)
                        FROM interests
                        JOIN generations ON interests.generationid = generations.generationid
                        JOIN simulations ON generations.simulationid = simulations.simulationid
                        WHERE simulations.parameterid = {parameter_id} 
                        AND generations.generation_count = {generation} 
                        AND interests.routebottleneck = {bottleneck};""")

            # 結果を取得
            rows = cur.fetchall()

            # 結果を二次元配列に格納
            width_counts_matrix[generation][10 - bottleneck // 10] = rows[0][0]

    pprint.pprint(width_counts_matrix)

    # 縦列→世代(昇順)、横行→widthを降順(100,90,80...0)、要素→その世代におけるそのwidthの割合
    proportions = [[0]*11 for _ in range(100)]
    for generation, width_count_list in enumerate(width_counts_matrix):
        total = sum(width_count_list)
        for i, width in enumerate(width_count_list):
            proportions[generation][i] = width * 100 / total

    pprint.pprint(proportions)

    # 転置する
    # 縦列→widthを降順(100,90,80...0)、横行→世代(昇順)、要素→その世代におけるそのwidthの割合
    transpose = list(map(list, (zip(*proportions))))

    # ! グラフ描写
    # 棒グラフの棒のカラー
    color = ['#4F71BE', '#DE8344', '#A5A5A5', '#F1C242', '#6A99D0',
             '#7EAB54', '#2D4374', '#934D21', '#636363', '#937424', '#355D8D']

    # 表示するラベルの用意(世代数)
    labels = list(range(len(transpose[0])))

    # bottomの準備(積み上げ用の変数)
    bottom = [0] * len(transpose[0])

    # プロットする色用のカウンタ
    color_count = 0

    for row in transpose:
        plt.bar(labels, row, width=1.0, bottom=bottom,
                color=color[color_count])
        bottom = [sum(x) for x in zip(bottom, row)]
        color_count += 1

    # グラフの設定
    plt.ylim((0, 100))
    plt.xlabel('Search Count')
    plt.ylabel('Percentage')
    plt.savefig("test.SVG")
    plt.show()


except Exception as e:
    print(e)
    conn.rollback()
    print(traceback.format_exc())

finally:
    # カーソルと接続を閉じる
    cur.close()
    conn.close()
