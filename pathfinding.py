from typing import Any


class Connection:
    def __init__(self, zone_a: str, zone_b, max_link_capacity: int, distance: int):
        self.from_hub = zone_a
        self.to_hub = zone_b
        self.max_link_capacity = max_link_capacity
        self.distance = distance


class Drone():
    def __init__(self, id: int, start_hub: "Hub", pathfinding: "PathFinding"):
        self.pathfinding = pathfinding
        self.id = id
        self.current_hub = start_hub
        self.wait_turns = 0
        self.path_follow: list[Hub] = [start_hub]

    def __str__(self):
        return f"D{self.id}-{self.current_hub.name}"

    def execute_turn(self):
        if self.wait_turn > 0:
            self.wait_turn -= 1
            return None 

        if not self.path_follow:
            return None

        next_hub = self.path_follow[0]

        if next_hub.can_receive_drone():
            if not next_hub.is_extremity:
                self.wait_turn -= 1

            self.current_hub = self.path_follow.pop(0)
            to_wait = self.pathfinding.distance[self.current_hub.type]

            if to_wait > 1:
                self.wait_turn = int(to_wait) - 1
            else:
                self.current_hub.current_drones += 1
            return f"D{self.id}-{self.current_hub.name}"
        return None


class Hub:
    def __init__(
        self,
        name: str,
        type: str,
        color: str,
        max_drones: int,
        coords: tuple[int, int],
        is_extremity: bool
    ):
        self.is_extremity = is_extremity
        self.name = name
        self.type = type
        self.color = color
        self.max_drones = max_drones
        self.coords = coords
        self.connections: dict["Hub", float] = {}
        self.current_drones = 0

    def add_connection(self, remote: "Hub", connection: Connection) -> None:
        self.connections.update({remote: connection})

    def __str__(self) -> str:
        connections = ", ".join([hub.name for hub in self.connections.keys()])
        return (
            f"Hub name: {self.name}, "
            f"Type: ({self.type}), "
            f"Connections: [{connections}]"
        )

    def can_receive_drone(self) -> bool:
        if self.is_extremity:
            return True
        return self.current_drones < self.max_drones


class PathFinding:
    def __init__(self, map_data: dict[str, Any]):
        self.distance = {
            "normal": 1.0,
            "blocked": -1.0,
            "restricted": 2.0,
            "priority": 0.5,
        }

        self.hubs: Hub = {
            hub["name"]: self._init_hub(hub, False) for hub in map_data["hubs"]
        }

        self.start_hub = self._init_hub(map_data["start_hub"], True)
        self.end_hub = self._init_hub(map_data["end_hub"], True)

        self.all_hubs = {
            hub.name: hub for hub in (list(self.hubs.values()) +
                                      [self.start_hub, self.end_hub])}
        self._init_connections(map_data["connections"], self.all_hubs)

        self.drones: dict[int, Drone] = {
            id: Drone(
                id=id,
                start_hub=self.start_hub
            )
            for id in range(1, map_data["nb_drones"] + 1)
        }

    def _init_hub(self, hub: dict, is_extremity: bool) -> dict[str, Any]:
        return Hub(
            name=hub["name"],
            type=hub["metadata"]["type"],
            color=hub["metadata"]["color"],
            max_drones=hub["metadata"]["max_drones"],
            coords=hub["coords"],
            is_extremity=is_extremity
        )

    def _init_connections(
        self,
        connections: dict,
        all_hubs: dict[str, Hub]
    ) -> None:
        for connection in connections:
            from_hub = all_hubs[connection["zone_a"]]
            to_hub = all_hubs[connection["zone_b"]]

            from_hub.add_connection(to_hub, Connection(
                zone_a=from_hub,
                zone_b=to_hub,
                max_link_capacity=connection["metadata"]["max_link_capacity"],
                distance=self.distance[to_hub.type]
            ))
