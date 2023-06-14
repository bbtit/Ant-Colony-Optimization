SELECT ants.*
FROM ants
JOIN generations ON ants.generationid = generations.generationid
JOIN simulations ON generations.simulationid = simulations.simulationid
WHERE simulations.parameterid = <parameter_id> AND generations.generation_count = 0;