from typing import Any


class Drone():
    def __init__(self, id: int, start_hub: "Hub"):
        self.id = id
        self.current_hub = start_hub

    def __str__(self):
        return f"D{self.id}-{self.current_hub.name}"


class Hub:
    def __init__(
        self,
        name: str,
        type: str,
        color: str,
        max_drones: int,
        coords: tuple[int, int]
    ):
        self.name = name
        self.type = type
        self.color = color
        self.max_drones = max_drones
        self.coords = coords
        self.connections: dict["Hub", float] = {}

    def add_connection(self, remote: "Hub", distance: float) -> None:
        self.connections.update({remote: distance})

    def __str__(self) -> str:
        connections = ", ".join([hub.name for hub in self.connections.keys()])
        return (
            f"Hub name: {self.name}, "
            f"Type: ({self.type}), "
            f"Connections: [{connections}]"
        )


class PathFinding:
    def __init__(self, map_data: dict[str, Any]):
        self.distance = {
            "normal": 1.0,
            "blocked": -1.0,
            "restricted": 2.0,
            "priority": 0.5,
        }

        self.hubs: Hub = {
            hub["name"]: self._init_hub(hub) for hub in map_data["hubs"]
        }

        self.start_hub = self._init_hub(map_data["start_hub"])
        self.end_hub = self._init_hub(map_data["end_hub"])

        self.all_hubs = {
            hub.name: hub for hub in (list(self.hubs.values()) +
                                      [self.start_hub, self.end_hub])}
        self._init_connections(map_data["connections"], self.all_hubs)

        self.drones: list[Drone] = {
            id: Drone(
                id=id,
                start_hub=self.start_hub
            )
            for id in range(1, map_data["nb_drones"] + 1)
        }

    def _init_hub(self, hub: dict) -> dict[str, Any]:
        return Hub(
            name=hub["name"],
            type=hub["metadata"]["type"],
            color=hub["metadata"]["color"],
            max_drones=hub["metadata"]["max_drones"],
            coords=hub["coords"]
        )

    def _init_connections(
        self,
        connections: dict,
        all_hubs: dict[str, Hub]
    ) -> None:
        for connection in connections:
            from_hub = all_hubs[connection["zone_a"]]
            to_hub = all_hubs[connection["zone_b"]]

            from_hub.add_connection(to_hub, self.distance[to_hub.type])
