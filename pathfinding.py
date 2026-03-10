from typing import Any
from itertools import count
import heapq


class Connection:
    def __init__(self, zone_a: str, zone_b, max_link_capacity: int, distance: int):
        self.from_hub = zone_a
        self.to_hub = zone_b
        self.max_link_capacity = max_link_capacity
        self.distance = distance


class Drone():
    def __init__(self, id: int, start_hub: "Hub", pathfinding: "PathFinding", path_follow: Any):
        self.pathfinding = pathfinding
        self.id = id
        self.current_hub = start_hub
        self.wait_turns = 0
        self.path_follow: list[Hub] = path_follow
        self.is_blocked = False
        self.blocked_count = 0

    def __str__(self):
        return f"D{self.id}-{self.current_hub.name}"

    def execute_turn(self):
        if self.wait_turns > 0:
            self.wait_turns -= 1
            if self.wait_turns == 0:
                if not self.current_hub.is_extremity:
                    self.current_hub.current_drones += 1
                return f"D{self.id}-{self.current_hub.name}"
            return None

        if not self.path_follow:
            return None

        next_hub = self.path_follow[0]

        if next_hub.can_receive_drone():
            if not self.current_hub.is_extremity:
                self.current_hub.current_drones -= 1
            
            self.current_hub = self.path_follow.pop(0)
            to_wait = self.pathfinding.distance[self.current_hub.type]

            if to_wait > 1:
                self.wait_turns = int(to_wait) - 1
                return None
            else:
                if not self.current_hub.is_extremity:
                    self.current_hub.current_drones += 1
                self.is_blocked = False
                self.blocked_count = 0
                return f"D{self.id}-{self.current_hub.name}"
        self.is_blocked = True
        self.blocked_count += 1
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
                start_hub=self.start_hub,
                pathfinding=self,
                path_follow=self.find_shortest_path(self.start_hub, self.end_hub)
            )
            for id in range(1, map_data["nb_drones"] + 1)
        }

        self.run_simulation()

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

    def find_shortest_path(self, start: Hub, end: Hub):
        counter = count() 

        queue = [(0.0, next(counter), start)]

        distances = {hub: float('inf') for hub in self.all_hubs.values()}
        distances[start] = 0.0
        predecessors = {}

        while queue:
            current_weight, _, u = heapq.heappop(queue)

            if current_weight > distances[u]:
                continue

            if u == end:
                break

            for v, connection in u.connections.items():
                if v.type == "blocked":
                    continue

                weight = self.distance[v.type]
                new_dist = distances[u] + weight

                if new_dist < distances[v]:
                    distances[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(queue, (new_dist, next(counter), v))

        path = []
        curr = end
        while curr in predecessors:
            path.append(curr)
            curr = predecessors[curr]

        return path[::-1]

    def run_simulation(self):
        turn = 1
        while any(d.current_hub != self.end_hub for d in self.drones.values()):
            moves_this_turn = []

            for drone in self.drones.values():
                if drone.current_hub == self.end_hub:
                    continue

                move_output = drone.execute_turn()

                if move_output:
                    moves_this_turn.append(move_output)
                
                if drone.is_blocked and drone.blocked_count > 2:
                    drone.path_follow = self.find_shortest_path(drone.current_hub, self.end_hub)

            if moves_this_turn:
                print(f"T{turn}: " + " ".join(moves_this_turn))
            
            turn += 1
            
            if turn > 1000: 
                break