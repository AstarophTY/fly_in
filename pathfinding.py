from typing import Any
import heapq


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
        self.finish = False

    def __str__(self):
        return f"D{self.id}-{self.current_hub.name}"

    def __repr__(self):
        return f"D{self.id}-{self.current_hub.name}"

    def execute_turn(self):
        if self.wait_turns > 0:
            self.wait_turns -= 1
            return None

        if not self.path_follow:
            self.finish = True
            return None

        next_hub = self.path_follow[0]

        if next_hub.can_receive_drone():
            if not self.current_hub.is_extremity:
                self.current_hub.current_drones -= 1

            self.current_hub = self.path_follow.pop(0)

            if not self.current_hub.is_extremity:
                self.current_hub.current_drones += 1

            to_wait = self.pathfinding.distance[self.current_hub.zone]
            if to_wait > 1:
                self.wait_turns = int(to_wait) - 1

        return str(self)


class Hub:
    def __init__(
        self,
        name: str,
        zone: str,
        color: str,
        max_drones: int,
        coords: tuple[int, int],
        is_extremity: bool
    ):
        self.is_extremity = is_extremity
        self.name = name
        self.zone = zone
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
            f"Zone: ({self.zone}), "
            f"Connections: [{connections}]"
            f"Drones: {self.current_drones}"
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
                start_hub=self.start_hub,
                pathfinding=self
            )
            for id in range(1, map_data["nb_drones"] + 1)
        }

        self._start_simulation()

    def _init_hub(self, hub: dict, is_extremity: bool) -> dict[str, Any]:
        return Hub(
            name=hub["name"],
            zone=hub["metadata"]["zone"],
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
            capacity = connection["metadata"]["max_link_capacity"]

            from_hub.add_connection(to_hub, Connection(
                zone_a=from_hub,
                zone_b=to_hub,
                max_link_capacity=capacity,
                distance=self.distance[to_hub.zone]
            ))
            to_hub.add_connection(from_hub, Connection(
                zone_a=to_hub,
                zone_b=from_hub,
                max_link_capacity=capacity,
                distance=self.distance[from_hub.zone]
            ))

    def _find_path(
        self,
        start: "Hub",
        end: "Hub",
        occupancy: dict[str, int] | None = None
    ) -> list["Hub"]:
        if occupancy is None:
            occupancy = {}

        heap = [(0.0, start.name)]
        costs: dict[str, float] = {start.name: 0.0}
        prev: dict[str, str | None] = {start.name: None}

        while heap:
            cost, name = heapq.heappop(heap)

            if cost > costs.get(name, float("inf")):
                continue

            if name == end.name:
                path = []
                while name is not None:
                    path.append(self.all_hubs[name])
                    name = prev[name]
                path.reverse()
                return path[1:]

            current = self.all_hubs[name]
            for connection in current.connections:
                connection_cost = self.distance.get(connection.zone, float("inf"))

                if connection_cost < 0:
                    continue

                if not connection.is_extremity:
                    alloc = occupancy.get(connection.name, 0)
                    if alloc >= connection.max_drones:
                        connection_cost += (alloc - connection.max_drones + 1) * 0.02

                new_cost = cost + connection_cost
                if new_cost < costs.get(connection.name, float("inf")):
                    costs[connection.name] = new_cost
                    prev[connection.name] = name
                    heapq.heappush(heap, (new_cost, connection.name))

        return []

    def _start_simulation(self):
        actions = []

        occupancy: dict[str, int] = {name: 0 for name in self.all_hubs}
        for drone in self.drones.values():
            path = self._find_path(self.start_hub, self.end_hub, occupancy)
            drone.path_follow = path
            for hub in path:
                if not hub.is_extremity:
                    occupancy[hub.name] += 1

        turn = 0
        max_turns = 10000
        while (
            turn < max_turns
            and any(
                not drone.finish and drone.current_hub != self.end_hub
                for drone in self.drones.values()
            )
        ):
            turn_actions = []
            turn += 1

            for drone in self.drones.values():
                if not drone.finish:
                    current_turn = drone.execute_turn()
                    if current_turn is not None:
                        turn_actions.append(current_turn)
            actions.append([" ".join(turn_actions)])
        print(actions)
        print(f"Simulation done in {turn} turn(s)")