from typing import Dict, Tuple, ClassVar, Self, TYPE_CHECKING, cast
import random
import pprint
import json
import math

class Params:
    def __init__(self, num_nodes:int, optimal_route_length:int, volatility:float, pheromone_min:int, pheromone_max:int, ttl:int, bata:int, generation_limit:int, simulation_count:int) -> None:
        self.num_nodes = num_nodes # ノード数
        self.optimal_route_length = optimal_route_length # 最適ルート長
        self.volatility = volatility # フェロモン揮発量
        self.pheromone_min = pheromone_min # フェロモンの最小値
        self.pheromone_max = pheromone_max # フェロモンの最大値
        self.ttl = ttl # パケットのTTL
        self.bata = bata # フェロモンの重み
        self.generation_limit = generation_limit # 1回のシミュレーションの世代数
        self.simulation_count = simulation_count # シミュレーション回数

    def get_attr_json(self) -> dict:
        return {
            "num_nodes" : self.num_nodes,
            "optimal_route_length" : self.optimal_route_length,
            "volatility" : self.volatility,
            "pheromone_min" : self.pheromone_min,
            "pheromone_max" : self.pheromone_max,
            "ttl" : self.ttl,
            "bata" : self.bata,
            "generation_limit" : self.generation_limit,
            "simulation_count" : self.simulation_count,
        }

class Link:
    def __init__(self, width:int, feromone:float) -> None:
        self.width = width
        self.feromone = feromone

    def get_attr_json(self) -> dict:
        return {
            "width" : self.width,
            "feromone" : self.feromone
        }

class Node:
    ID:ClassVar[int] = 0

    def __init__(self) -> None:
        self.id = Node.ID # クラス変数をもとにしたノードのID
        self.neighbors:dict[Node, Link] = {}
        Node.ID += 1 # クラス変数をインクリメント

    def connect(self, target_node:Self, width:int, pheromone:int) -> None:
        self.neighbors[target_node] = Link(width, pheromone)
        target_node.neighbors[self] = Link(width, pheromone)

    def get_attr_json(self) -> dict:
        tmp = {}
        for node, link in self.neighbors.items():
            tmp.update({"node" + str(node.id) : link.get_attr_json()})
        return {"node" + str(self.id) : tmp}

class Packet:
    def __init__(self, source:Node, destination:Node) -> None:
        self.source = source
        self.destination = destination
        self.current_node = source
        self.route:list[Node] = [source]
        self.route_width:list[int] = []
        self.route_bottoleneck:int = 2**8
        self.movable:bool = True
        
    def is_at_destination(self) -> bool:
        return self.current_node == self.destination
        
    def update_attr(self, next_node:Node) -> None:
        self.route.append(next_node)
        self.route_width.append(self.current_node.neighbors[next_node].width)
        self.route_bottoleneck = min(self.route_bottoleneck, self.current_node.neighbors[next_node].width)
        self.current_node = next_node

    def set_unmovable(self) -> None:
        self.movable = False

    def get_attr_json(self) -> dict:
        return {
            "source" : self.source.id,
            "destination" : self.destination.id,
            "route" : [node.id for node in self.route],
            "route_width" : self.route_width,
            "route_bottoleneck" : self.route_bottoleneck,
        }

class Ant(Packet):
    def hop(self, params:Params) -> None:
        unvisited_nodes = [node for node in self.current_node.neighbors.keys() if node not in self.route]
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
        unvisited_links = [self.current_node.neighbors[node] for node in self.current_node.neighbors.keys() if node not in self.route]
        unvisited_links_width = [link.width for link in unvisited_links]
        unvisited_links_pheromone = [link.feromone for link in unvisited_links]
        weights = [ (width ** params.bata) * pheromone for width, pheromone in zip(unvisited_links_width, unvisited_links_pheromone)]
        next_node = random.choices(unvisited_nodes, weights=weights)[0]
        self.update_attr(next_node)
        return
    
    def hop_if_movable(self, params:Params) -> None:
        while self.movable:
            self.hop(params)
        
    def get_attr_json(self) -> dict:
        return {"ant" : super().get_attr_json()}
    

class Rand(Packet):
    def hop(self):
        unvisited_nodes = [node for node in self.current_node.neighbors.keys() if node not in self.route]
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
    
    def hop_if_movable(self, params:Params) -> None:
        if self.movable:
            self.hop()
        else:
            return
        
    def get_attr_json(self) -> dict:
        return {"rand" : super().get_attr_json()}

class Interest(Packet):
    def hop(self):
        unvisited_nodes = [node for node in self.current_node.neighbors.keys() if node not in self.route]
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
        next_node = max(unvisited_nodes, key=lambda node: node.neighbors[self.current_node].feromone)
        self.update_attr(next_node)
        return
    
    def hop_if_movable(self, params:Params) -> None:
        if self.movable:
            self.hop()
        else:
            return
        
    def get_attr_json(self) -> dict:
        return {"interest" : super().get_attr_json()}

class Network:
    def __init__(self) -> None:
        self.nodes:list[Node] = []
        self.start_node:Node|None = None
        self.end_node:Node|None = None
        self.optimal_route:list[Node]|None = None

    def make_ba_model(self, params:Params, edge_num:int) -> None:
        self.nodes = [Node() for _ in range(params.num_nodes)] # 別々のノードを作成

        # 3つのノードから初期ネットワーク作成
        self.nodes[0].connect(self.nodes[1], random.randint(1,10) * 10, params.pheromone_min)
        self.nodes[1].connect(self.nodes[2], random.randint(1,10) * 10, params.pheromone_min)
        self.nodes[2].connect(self.nodes[0], random.randint(1,10) * 10, params.pheromone_min)

        # BAモデルの次数分布を格納するリスト
        nodes_degree = [0 for _ in range(params.num_nodes)]
        nodes_degree[0] = 2
        nodes_degree[1] = 2
        nodes_degree[2] = 2
        
        # 次数分布を基に接続先ノードを重複なし重み付き乱択しBAモデル作成
        for i in range(3, params.num_nodes):
            candidate_nodes_id = [j for j in range(i)] # 接続先候補ノードのid
            candidate_nodes_weight = nodes_degree[:i] # 接続先候補ノードの重み
            target_nodes_id = []
            
            for _ in range(edge_num):
                chosen_id = random.choices(candidate_nodes_id, weights=candidate_nodes_weight)[0] # 重み付き乱択で接続先候補ノードを選択
                target_nodes_id.append(chosen_id)
                del candidate_nodes_weight[candidate_nodes_id.index(chosen_id)] # 選択したノードの重みを削除
                del candidate_nodes_id[candidate_nodes_id.index(chosen_id)] # 選択したノードのidを削除

            for j in target_nodes_id:
                self.nodes[i].connect(self.nodes[j], random.randint(1,10) * 10, params.pheromone_min)

            nodes_degree[i] = edge_num

    def make_optimal_route(self, params:Params) -> None:
        # 最適ルートを作成
        # self.start_nodeをself.nodesからランダムに選択
        self.start_node = random.choice(self.nodes)
        # self.start_nodeからparams.optimal_route_length分のnodeをランダムに移動した経路を最適ルートoptimal_routeとする
        # 最適ルートoptimal_routeの最後のnodeをself.end_nodeとする
        self.end_node = self.start_node
        optimal_route = [self.start_node]
        for _ in range(params.optimal_route_length):
            unvisited_nodes = [node for node in self.end_node.neighbors.keys() if node not in optimal_route]
            self.end_node = random.choice(unvisited_nodes)
            optimal_route.append(self.end_node)
        # 最適経路のnode間のLinkのwidthを100にする
        for i in range(len(optimal_route) - 1):
            optimal_route[i].neighbors[optimal_route[i + 1]].width = 100
        self.optimal_route = optimal_route

    def add_pheromone_to_ant_route(self, ant:Ant) -> None:
        # antの辿った経路のフェロモン値にant.route_bottoleneck分を加算する
        for i in range(len(ant.route) - 1):
            ant.route[i].neighbors[ant.route[i + 1]].feromone += ant.route_bottoleneck

    def volitile_pheromone(self, params:Params) -> None:
        # self.nodesのすべてのNodeのneighborsのLinkのフェロモンを揮発(×params.bata)させる
        for node in self.nodes:
            for link in node.neighbors.values():
                tmp = math.floor(link.feromone * params.bata)
                if tmp < params.pheromone_min:
                    link.feromone = params.pheromone_min
                elif tmp > params.pheromone_max:
                    link.feromone = params.pheromone_max
                else:
                    link.feromone = tmp

    def get_attr_json(self) -> dict:
        optimal_route_dict:dict[str,list[int]]|dict[str,None] # 下の分岐によって型が変わりmypyに引っかかるのでUnion型として定義
        if self.optimal_route is not None:
            optimal_route_dict = {"optimal" : [node.id for node in self.optimal_route]}
        else:
            optimal_route_dict = {"optimal" : self.optimal_route}
        tmp = optimal_route_dict
        for node in self.nodes:
            tmp.update(node.get_attr_json())
        return {"network" : tmp}
    
class SimulationLogger:
    def __init__(self, file_path:str, file_name:str) -> None:
        self.file_path = file_path
        self.file_name = file_name
        self.log:dict = {}

    def save_params(self, params:Params) -> None:
        self.log["params"] = params.get_attr_json()

    def prepare_dict_for_simulation(self, simulation_count:int) -> None:
        self.log["simulation" + str(simulation_count)] = {}

    def prepare_dict_for_generation(self, simulation_count:int, generation_count:int) -> None:
        self.log["simulation" + str(simulation_count)]["generation" + str(generation_count)] = {}

    def save_network(self, simulation_count:int, generation_count:int, network:Network) -> None:
        self.log["simulation" + str(simulation_count)]["generation" + str(generation_count)].update(network.get_attr_json())

    def save_ant(self, simulation_count:int, generation_count:int, ant:Ant) -> None:
        self.log["simulation" + str(simulation_count)]["generation" + str(generation_count)].update(ant.get_attr_json())

    def save_interest(self, simulation_count:int, generation_count:int, interest:Interest) -> None:
        self.log["simulation" + str(simulation_count)]["generation" + str(generation_count)].update(interest.get_attr_json())

    def output_log(self) -> None:
        with open(self.file_path + self.file_name, "w") as f:
            json.dump(self.log, f, indent=6, ensure_ascii=False)

class Simulation:
    SIMULATION_COUNT:ClassVar[int] = -1

    def __init__(self, logger:SimulationLogger) -> None:
        self.network = Network()
        self.ant:Ant|None = None
        self.rand:Rand|None = None
        self.interest:Interest|None = None
        self.generation_count:int = 0
        self.logger = logger
        Simulation.SIMULATION_COUNT += 1

    def run(self, params:Params) -> None:
        # このシミュレーションのログを保存するための辞書を作成
        self.logger.prepare_dict_for_simulation(Simulation.SIMULATION_COUNT)
        # ネットワーク作成
        self.network.make_ba_model(params, 3)
        # 最適ルート作成
        self.network.make_optimal_route(params)

        # network.start_nodeとnetwork.end_nodeがNodeクラスであることを確認
        if isinstance(self.network.start_node, Node) and isinstance(self.network.end_node, Node):
            pass
        else:
            raise TypeError("self.network.start_node is not Node class")

        while self.generation_count < params.generation_limit:
            # この世代のログを保存するための辞書を作成
            self.logger.prepare_dict_for_generation(Simulation.SIMULATION_COUNT, self.generation_count)
            # networkのログを保存
            self.logger.save_network(Simulation.SIMULATION_COUNT, self.generation_count, self.network)

            # antとinterestの生成
            self.ant = Ant(self.network.start_node, self.network.end_node)
            self.interest = Interest(self.network.start_node, self.network.end_node)
            
            # antの移動
            self.ant.hop_if_movable(params)
            # 目的地に到達していたらフェロモン付加
            if self.ant.is_at_destination():
                self.network.add_pheromone_to_ant_route(self.ant)
            # antのログを保存
            self.logger.save_ant(Simulation.SIMULATION_COUNT, self.generation_count, self.ant)
            # antをNoneにして消去
            self.ant = None
            
            # interestの移動
            self.interest.hop_if_movable(params)
            # interestのログを保存
            self.logger.save_interest(Simulation.SIMULATION_COUNT, self.generation_count, self.interest)
            # interestをNoneにして消去
            self.interest = None

            # フェロモン揮発
            self.network.volitile_pheromone(params)

            # 世代のカウントをインクリメント
            self.generation_count += 1


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
                    simulation_count=2)
    
    # SimulationLoggerインスタンス作成
    logger = SimulationLogger("./", "result.json")
    logger.save_params(params)
    
    # シミュレーションをparams.simulation_count回実行
    for _ in range(params.simulation_count):
        # Simulationインスタンス作成
        simulation = Simulation(logger)
        # シミュレーション実行
        simulation.run(params)

    # pprint.pprint(logger.log, width=40)
    logger.output_log()