# 通常ACO
# 出力はDBに格納
from typing import Dict, Tuple, ClassVar, Self, TYPE_CHECKING, cast, Any
import random
import traceback
import math
import psycopg2
from multiprocessing import Pool


class Params:
    def __init__(self, num_nodes: int, optimal_route_length: int, volatility: float, pheromone_min: int, pheromone_max: int, ttl: int, bata: int, generation_limit: int, simulation_count: int) -> None:
        self.id = None  # パラメータID
        self.num_nodes = num_nodes  # ノード数
        self.optimal_route_length = optimal_route_length  # 最適ルート長
        self.volatility = volatility  # フェロモン揮発量
        self.pheromone_min = pheromone_min  # フェロモンの最小値
        self.pheromone_max = pheromone_max  # フェロモンの最大値
        self.ttl = ttl  # パケットのTTL
        self.bata = bata  # フェロモンの重み
        self.generation_limit = generation_limit  # 1回のシミュレーションの世代数
        self.simulation_count = simulation_count  # シミュレーション回数

    def generate_insert_query(self) -> str:
        return f"INSERT INTO parameters (numberofnodes, optimalpathlength, volatility, minpheromone, maxpheromone, ttl, bata, generationlimit) VALUES ({self.num_nodes}, {self.optimal_route_length}, {self.volatility}, {self.pheromone_min}, {self.pheromone_max}, {self.ttl}, {self.bata}, {self.generation_limit},);"

    def generate_insert_or_return_id_query(self) -> str:
        # 既存の行と競合する場合にidを返すクエリ
        return f"INSERT INTO parameters (numberofnodes, optimalpathlength, volatility, minpheromone, maxpheromone, ttl, bata, generationlimit) VALUES ({self.num_nodes}, {self.optimal_route_length}, {self.volatility}, {self.pheromone_min}, {self.pheromone_max}, {self.ttl}, {self.bata}, {self.generation_limit}) ON CONFLICT (numberofnodes, optimalpathlength, volatility, minpheromone, maxpheromone, ttl, bata, generationlimit) DO NOTHING RETURNING parameterid;"

    def generate_select_query(self) -> str:
        return f"SELECT parameterid FROM parameters WHERE numberofnodes = {self.num_nodes} AND optimalpathlength = {self.optimal_route_length} AND volatility = {self.volatility} AND minpheromone = {self.pheromone_min} AND maxpheromone = {self.pheromone_max} AND ttl = {self.ttl} AND bata = {self.bata} AND generationlimit = {self.generation_limit};"


class Link:
    def __init__(self, width: int, feromone: float) -> None:
        self.width = width
        self.pheromone = feromone


class Node:
    def __init__(self) -> None:
        self.id: int = None
        self.neighbors: dict[Node, Link] = {}

    def connect(self, target_node: Self, width: int, pheromone: int) -> None:
        self.neighbors[target_node] = Link(width, pheromone)
        target_node.neighbors[self] = Link(width, pheromone)

    def generate_insert_query(self, simulation_id) -> str:
        return f'INSERT INTO Nodes (simulationid, Num_of_connections) VALUES ({simulation_id},{len(self.neighbors)});'


class Packet:
    def __init__(self, source: Node, destination: Node) -> None:
        self.source = source
        self.destination = destination
        self.current_node = source
        self.route: list[Node] = [source]
        self.route_width: list[int] = []
        self.route_bottoleneck: int = 2**8
        self.movable: bool = True

    def is_at_destination(self) -> bool:
        return self.current_node == self.destination

    def update_attr(self, next_node: Node) -> None:
        self.route.append(next_node)
        self.route_width.append(self.current_node.neighbors[next_node].width)
        self.route_bottoleneck = min(
            self.route_bottoleneck, self.current_node.neighbors[next_node].width)
        self.current_node = next_node

    def set_unmovable(self) -> None:
        self.movable = False


class Ant(Packet):
    def hop(self, params: Params) -> None:
        unvisited_nodes = [
            node for node in self.current_node.neighbors.keys() if node not in self.route]
        # current_nodeのneighborsに未訪問ノードがないならば属性を更新し終了
        if len(unvisited_nodes) == 0:
            self.set_unmovable()
            return

        # current_nodeのneighborsにdestinationが含まれているか確認
        # current_nodeのneighborsにdestinationが含まれている場合
        if self.destination in self.current_node.neighbors.keys():
            # destinationに到達したので属性を更新し終了
            self.update_attr(self.destination)
            self.set_unmovable()
            return

        # current_nodeのneighborsにdestinationが含まれていない場合
        unvisited_links = [self.current_node.neighbors[node]
                           for node in self.current_node.neighbors.keys() if node not in self.route]
        unvisited_links_width = [link.width for link in unvisited_links]
        unvisited_links_pheromone = [link.pheromone for link in unvisited_links]
        weights = [(width ** params.bata) * pheromone for width,
                   pheromone in zip(unvisited_links_width, unvisited_links_pheromone)]
        next_node = random.choices(unvisited_nodes, weights=weights)[0]
        self.update_attr(next_node)
        return

    def hop_if_movable(self, params: Params) -> None:
        while self.movable:
            self.hop(params)

    def get_insert_query(self, generation_id: int) -> str:
        route_node_id = [node.id for node in self.route]
        return f'INSERT INTO Ants (GenerationId, SourceNodeID, DestinationNodeID, RouteNodesID, RouteWidths, RouteBottleneck) VALUES ({generation_id}, {self.source.id}, {self.destination.id}, ARRAY{route_node_id}, ARRAY{self.route_width}, {self.route_bottoleneck});'


class Rand(Packet):
    def hop(self):
        unvisited_nodes = [
            node for node in self.current_node.neighbors.keys() if node not in self.route]
        # current_nodeのneighborsに未訪問ノードがないならば属性を更新し終了
        if len(unvisited_nodes) == 0:
            self.set_unmovable()
            return

        # current_nodeのneighborsにdestinationが含まれているか確認
        # current_nodeのneighborsにdestinationが含まれている場合
        if self.destination in self.current_node.neighbors.keys():
            # destinationに到達したので属性を更新し終了
            self.update_attr(self.destination)
            self.set_unmovable()
            return

        # current_nodeのneighborsにdestinationが含まれていない場合
        next_node = random.choice(unvisited_nodes)
        self.update_attr(next_node)
        return

    def hop_if_movable(self, params: Params) -> None:
        if self.movable:
            self.hop()
        else:
            return

    def get_insert_query(self, generation_id: int) -> str:
        route_node_id = [node.id for node in self.route]
        return f'INSERT INTO Rands (GenerationId, SourceNodeID, DestinationNodeID, RouteNodesID, RouteWidths, RouteBottleneck) VALUES ({generation_id}, {self.source.id}, {self.destination.id}, ARRAY{route_node_id}, ARRAY{self.route_width}, {self.route_bottoleneck});'


class Interest(Packet):
    def hop(self) -> None:
        unvisited_nodes = [
            node for node in self.current_node.neighbors.keys() if node not in self.route]
        # current_nodeのneighborsに未訪問ノードがないならば属性を更新し終了
        if len(unvisited_nodes) == 0:
            self.set_unmovable()
            return

        # current_nodeのneighborsにdestinationが含まれているか確認
        # current_nodeのneighborsにdestinationが含まれている場合
        if self.destination in self.current_node.neighbors.keys():
            # destinationに到達したので属性を更新し終了
            self.update_attr(self.destination)
            self.set_unmovable()
            return

        # current_nodeのneighborsにdestinationが含まれていない場合
        # neighborの中で最もフェロモンが多いノードを選択
        next_node = max(
            unvisited_nodes, key=lambda node: node.neighbors[self.current_node].pheromone)
        self.update_attr(next_node)
        return

    def hop_if_movable(self, params: Params) -> None:
        if self.movable:
            self.hop()
        else:
            return

    def get_insert_query(self, generation_id: int) -> str:
        route_node_id = [node.id for node in self.route]
        return f'INSERT INTO Interests (GenerationId, SourceNodeID, DestinationNodeID, RouteNodesID, RouteWidths, RouteBottleneck) VALUES ({generation_id}, {self.source.id}, {self.destination.id}, ARRAY{route_node_id}, ARRAY{self.route_width}, {self.route_bottoleneck});'


class Network:
    def __init__(self) -> None:
        self.nodes: list[Node] = []
        self.start_node: Node | None = None
        self.end_node: Node | None = None
        self.optimal_route: list[Node] | None = None

    def yield_nodes(self, params: Params) -> None:
        self.nodes = [Node() for _ in range(params.num_nodes)]

    def make_ba_model(self, params: Params, edge_num: int) -> None:
        # 3つのノードから初期ネットワーク作成
        self.nodes[0].connect(self.nodes[1], random.randint(
            1, 10) * 10, params.pheromone_min)
        self.nodes[1].connect(self.nodes[2], random.randint(
            1, 10) * 10, params.pheromone_min)
        self.nodes[2].connect(self.nodes[0], random.randint(
            1, 10) * 10, params.pheromone_min)

        # BAモデルの次数分布を格納するリスト
        nodes_degree = [0 for _ in range(params.num_nodes)]
        nodes_degree[0] = 2
        nodes_degree[1] = 2
        nodes_degree[2] = 2

        # 次数分布を基に接続先ノードを重複なし重み付き乱択しBAモデル作成
        for i in range(3, params.num_nodes):
            candidate_nodes_id = [j for j in range(i)]  # 接続先候補ノードのid
            candidate_nodes_weight = nodes_degree[:i]  # 接続先候補ノードの重み
            target_nodes_id = []

            for _ in range(edge_num):
                chosen_id = random.choices(candidate_nodes_id, weights=candidate_nodes_weight)[
                    0]  # 重み付き乱択で接続先候補ノードを選択
                target_nodes_id.append(chosen_id)
                del candidate_nodes_weight[candidate_nodes_id.index(
                    chosen_id)]  # 選択したノードの重みを削除
                del candidate_nodes_id[candidate_nodes_id.index(
                    chosen_id)]  # 選択したノードのidを削除

            for j in target_nodes_id:
                self.nodes[i].connect(self.nodes[j], random.randint(
                    1, 10) * 10, params.pheromone_min)

            nodes_degree[i] = edge_num

    def make_optimal_route(self, params: Params) -> None:
        # 最適ルートを作成
        # self.start_nodeをself.nodesからランダムに選択
        self.start_node = random.choice(self.nodes)
        # self.start_nodeからparams.optimal_route_length分のnodeをランダムに移動した経路を最適ルートoptimal_routeとする
        # 最適ルートoptimal_routeの最後のnodeをself.end_nodeとする
        self.end_node = self.start_node
        optimal_route = [self.start_node]
        for _ in range(params.optimal_route_length):
            unvisited_nodes = [
                node for node in self.end_node.neighbors.keys() if node not in optimal_route]
            self.end_node = random.choice(unvisited_nodes)
            optimal_route.append(self.end_node)
        # 最適経路のnode間のLinkのwidthを100にする
        for i in range(len(optimal_route) - 1):
            optimal_route[i].neighbors[optimal_route[i + 1]].width = 100
        self.optimal_route = optimal_route

    def add_pheromone_to_ant_route(self, ant: Ant) -> None:
        # antの辿った経路のフェロモン値にant.route_bottoleneck分を加算する
        for i in range(len(ant.route) - 1):
            ant.route[i].neighbors[ant.route[i + 1]
                                   ].pheromone += ant.route_bottoleneck

    def volitile_pheromone(self, params: Params) -> None:
        # self.nodesのすべてのNodeのneighborsのLinkのフェロモンを揮発(×params.bata)させる
        for node in self.nodes:
            for link in node.neighbors.values():
                tmp = math.floor(link.pheromone * params.volatility)
                if tmp < params.pheromone_min:
                    link.pheromone = params.pheromone_min
                elif tmp > params.pheromone_max:
                    link.pheromone = params.pheromone_max
                else:
                    link.pheromone = tmp


class DBLogger:
    def __init__(self, user: str, password: str, host: str, db_name: str, port: str) -> None:
        self.dbname = db_name
        self.user = user
        self.password = password
        self.host = host
        self.connector = None
        self.cursor = None

    def connect(self):
        self.connector = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host
        )
        self.cursor = self.connector.cursor()

    # 任意のクエリを実行し、結果を返さない
    def execute_query(self, query: int, params=None) -> None:
        self.cursor.execute(query, params)

    # 任意のクエリを実行し、結果を返す
    def fetch_result(self, query: int, params=None) -> list[tuple[Any]]:
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # INSERTクエリを実行し、生成されたIDを返す
    def insert_and_get_id(self, query: int, params=None) -> int:
        self.cursor.execute(query, params)
        self.cursor.execute("SELECT LASTVAL();")
        return self.cursor.fetchone()[0]

    def insert_conflict(self, query: int, params=None) -> int:
        id = self.cursor.execute(query, params)
        return id

    # 変更を確定
    def commit(self):
        self.connector.commit()

    # 変更を破棄
    def rollback(self):
        self.connector.rollback()

    # データベース接続を閉じる
    def close(self) -> None:
        self.cursor.close()
        self.connector.close()


class Simulation:
    def __init__(self, logger: DBLogger, params: Params) -> None:
        self.id = None
        self.params: Params = params
        self.logger = logger

        self.network = Network()
        self.ant: Ant | None = None
        self.rand: Rand | None = None
        self.interest: Interest | None = None

        self.generation_count: int = 0

    def generate_insert_query(self) -> str:
        return f'INSERT INTO simulations (ParameterID) VALUES ({self.params.id});'


def main(params: Params):
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
