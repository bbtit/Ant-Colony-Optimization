CREATE TABLE Parameters (
    ParameterID SERIAL PRIMARY KEY,
    NumberOfNodes int,
    Volatility float,
    MinPheromone float,
    MaxPheromone float,
    TTL int,
    GenerationLimit int,
    SimulationLimit int,
    optimalPathLength int,
    bata float
);
-- unique制約をつける

CREATE TABLE Simulations (
    SimulationID SERIAL PRIMARY KEY,
    ParameterID int,
    FOREIGN KEY (ParameterID) REFERENCES Parameters(ParameterID)
);

CREATE TABLE Generations (
    GenerationID BIGSERIAL PRIMARY KEY,
    SimulationID int,
    FOREIGN KEY (SimulationID) REFERENCES Simulations(SimulationID)
);

CREATE TABLE Nodes (
    NodeID BIGSERIAL PRIMARY KEY,
    SimulationID int,
    Num_of_Generations int,
    FOREIGN KEY (SimulationID) REFERENCES Simulations(SimulationID)
);

CREATE TABLE Connections (
    GenerationID Bigint,
    StartNodeID Bigint,
    EndNodeID Bigint,
    Width int,
    Pheromone int,
    FOREIGN KEY (GenerationID) REFERENCES Generations(GenerationID),
    FOREIGN KEY (StartNodeID) REFERENCES Nodes(NodeID),
    FOREIGN KEY (EndNodeID) REFERENCES Nodes(NodeID),
    PRIMARY KEY (GenerationID, StartNodeID, EndNodeID)
);

CREATE TABLE Ants (
    GenerationID Bigint,
    SourceNodeID Bigint,
    DestinationNodeID Bigint,
    RouteNodesID Bigint[],
    RouteWidths int[],
    RouteBottleneck int,
    FOREIGN KEY (GenerationID) REFERENCES Generations(GenerationID),
    FOREIGN KEY (SourceNodeID) REFERENCES Nodes(NodeID),
    FOREIGN KEY (DestinationNodeID) REFERENCES Nodes(NodeID),
    PRIMARY KEY (GenerationID)
);

CREATE TABLE Interests (
    GenerationID Bigint,
    SourceNodeID Bigint,
    DestinationNodeID Bigint,
    RouteNodesID Bigint[],
    RouteWidths int[],
    RouteBottleneck int,
    FOREIGN KEY (GenerationID) REFERENCES Generations(GenerationID),
    FOREIGN KEY (SourceNodeID) REFERENCES Nodes(NodeID),
    FOREIGN KEY (DestinationNodeID) REFERENCES Nodes(NodeID),
    PRIMARY KEY (GenerationID)
);

CREATE TABLE Rands (
    GenerationID Bigint,
    SourceNodeID Bigint,
    DestinationNodeID Bigint,
    RouteNodesID Bigint[],
    RouteWidths int[],
    RouteBottleneck int,
    FOREIGN KEY (GenerationID) REFERENCES Generations(GenerationID),
    FOREIGN KEY (SourceNodeID) REFERENCES Nodes(NodeID),
    FOREIGN KEY (DestinationNodeID) REFERENCES Nodes(NodeID),
    PRIMARY KEY (GenerationID)
);
