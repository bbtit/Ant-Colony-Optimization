# 可変フェロモン最小値方式
# ノードのフェロモン最小値をノードのエッジ数によって変化させる
# TODO ノードクラスの属性にフェロモン最小値を追加
# TODO フェロモン最小値をネットワーク作成時の初期値として設定する関数を作成
# TODO 揮発時にフェロモン最小値以下になった場合はフェロモン最小値にするように変更
# TODO 新しいデータベースを作成
# TODO データベースのテーブルを変更


from base import Params, Link, Node, Packet, Ant, Interest, Rand, Network, DBLogger, Simulation
from typing import Dict, Tuple, ClassVar, Self, TYPE_CHECKING, cast, Any
import random
import traceback
import math
import psycopg2
from multiprocessing import Pool

# ネットワーク作成後にノードの次元数に基づいたフェロモン最小値を代入
def set_pheromone_based_on_dimension(self: Network, params: Params) -> None:
    for node in self.nodes:
        for link in node.neighbors.values():
            degree = len(node.neighbors)
            link.pheromone = params.pheromone_min * 3 // degree

# 次元数によるフェロモン最小値を用いたフェロモン揮発
def volitile_pheromone_based_on_dimension(self: Network, params: Params) -> None:
    for node in self.nodes:
        for link in node.neighbors.values():
            degree = len(node.neighbors)
            floor = params.pheromone_min * 3 * degree
            tmp = math.floor(link.pheromone * params.bata)
            if tmp < floor:
                link.pheromone = floor
            elif tmp > params.pheromone_max:
                link.pheromone = params.pheromone_max
            else:
                link.pheromone = tmp

def main(params: Params):
    
    # Networkクラスにset_pheromone_based_on_dimensionメソッド追加
    Network.set_pheromone_based_on_dimension = set_pheromone_based_on_dimension

    # Networkクラスのvolitile_pheromoneメソッドを差し替え
    Network.volitile_pheromone = volitile_pheromone_based_on_dimension

    # ネットワーク作成後にset_pheromone_based_on_dimension()を実行する手順を追加
    try:
        # DBLoggerインスタンス作成
        dblogger = DBLogger("asaken_n40", "asaken_N40",
                            "localhost", "simulation", "5432")

        dblogger.connect()

        # パラメータを登録&パラメータIDを取得
        params.id = dblogger.insert_conflict(
            params.generate_insert_or_return_id_query())
        print(params.id)
        if params.id is None:
            params.id: int = dblogger.fetch_result(
                params.generate_select_query())[0][0]
            print(params.id)

        # Simulationインスタンス作成
        simulation = Simulation(dblogger, params)

        # シミュレーションを登録&シミュレーションIDを取得
        simulation.id = dblogger.insert_and_get_id(
            simulation.generate_insert_query())

        # 任意の個数ノードインスタンスを作成
        simulation.network.yield_nodes(params)

        # BAモデルになるようにノードを接続
        simulation.network.make_ba_model(params, 3)

        # 最適ルートを作成
        simulation.network.make_optimal_route(params)

        # ノードのフェロモンをノードのエッジ数によって変化させる
        simulation.network.set_pheromone_based_on_dimension(params)

        # ノードを登録&ノードIDを取得
        for node in simulation.network.nodes:
            node.id = dblogger.insert_and_get_id(
                node.generate_insert_query(simulation.id))

        # 任意の回数Generationを繰り返す
        for generation_count in range(params.generation_limit):

            # Genaerationを登録&GenerationIDを取得
            generation_id = dblogger.insert_and_get_id(
                f'INSERT INTO generations (simulationid, generation_count) VALUES ({simulation.id},{generation_count});')

            # Connectionsを登録
            for startnode in simulation.network.nodes:
                for endnode, link in node.neighbors.items():
                    dblogger.insert_and_get_id(
                        f'INSERT INTO connections (GenerationID, StartNodeID, EndNodeID, Pheromone, Width) VALUES ({generation_id},{startnode.id},{endnode.id},{link.pheromone},{link.width});')

            # antとinterestの生成
            simulation.ant = Ant(
                simulation.network.start_node, simulation.network.end_node)
            simulation.interest = Interest(
                simulation.network.start_node, simulation.network.end_node)

            # antの移動
            simulation.ant.hop_if_movable(params)

            # 目的地に到達していたらフェロモン付加
            if simulation.ant.is_at_destination():
                simulation.network.add_pheromone_to_ant_route(simulation.ant)

            # antの結果を登録
            dblogger.execute_query(
                simulation.ant.get_insert_query(generation_id))

            # antをNoneにして消去
            simulation.ant = None

            # interestの移動
            simulation.interest.hop_if_movable(params)

            # interestの結果を登録
            dblogger.execute_query(
                simulation.interest.get_insert_query(generation_id))

            # interestをNoneにして消去
            simulation.interest = None

            # フェロモン揮発
            simulation.network.volitile_pheromone(params)

        dblogger.commit()

    except Exception as e:
        print(e)
        dblogger.rollback()
        print(traceback.format_exc())

    finally:
        dblogger.close()


if __name__ == "__main__":
    # パラメータを設定
    params = Params(num_nodes=5,
                    optimal_route_length=2,
                    volatility=0.99,
                    pheromone_min=100,
                    pheromone_max=2**20,
                    ttl=100,
                    bata=1,
                    generation_limit=2,
                    simulation_count=1)

    with Pool() as p:
        p.map(main, [params] * params.simulation_count)