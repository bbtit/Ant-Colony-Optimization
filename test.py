import json
import pprint

json_open = open('result.json', 'r')

json_load = json.load(json_open)

# print(json_load['simulation0']["generation0"]["network"])

node_id_of_ant_route:list[int] = json_load['simulation0']["generation0"]["ant"]["route"]
pprint.pprint(node_id_of_ant_route)

node_of_ant_route_before = {}
for i in node_id_of_ant_route:
  node:dict[str,dict[str,int]] = json_load['simulation0']["generation0"]["network"]["node" + str(i)]
  # ! updateのせいで重複したやつが上書きされてる
  node_of_ant_route_before.update(node)

pprint.pprint(node_of_ant_route_before,width=20)

node_of_ant_route_after = {}
for i in node_id_of_ant_route:
  node:dict[str,dict[str,int]] = json_load['simulation0']["generation1"]["network"]["node" + str(i)]
  node_of_ant_route_after.update(node)

pprint.pprint(node_of_ant_route_after,width=20)