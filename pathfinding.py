from typing import Any
import heapq


class Connection:
    """Represent a connection between two hubs.
    """

    def __init__(
        self,
        zone_a: "Hub",
        zone_b: "Hub",
        max_link_capacity: int,
        distance: float
    ):
        """Build connection object.

        Args:
            zone_a (Hub): Start hub of connection
            zone_b (Hub): Target hub of connection
            max_link_capacity (int): Max drones allowed on this link
            distance (float): Cost to enter the target hub zone
        """
        self.from_hub = zone_a
        self.to_hub = zone_b
        self.max_link_capacity = max_link_capacity
        self.distance = distance


class Drone():
    """Represent a drone moving through hubs.
    """

    def __init__(
        self,
        id: int,
        start_hub: "Hub",
        pathfinding: "PathFinding"
    ) -> None:
        """Build drone object.

        Args:
            id (int): Unique id of the drone
            start_hub (Hub): Initial hub of drone
            pathfinding (PathFinding): Pathfinding context
        """
        self.pathfinding = pathfinding
        self.id = id
        self.current_hub = start_hub
        self.wait_turns = 0
        self.path_follow: list[Hub] = [start_hub]
        self.finish = False

    def __str__(self) -> str:
        """Return compact drone position.

        Returns:
            str: Drone as D<id>-<hub_name>
        """
        return f"D{self.id}-{self.current_hub.name}"

    def execute_turn(self) -> str | None:
        """Execute one simulation turn for this drone.

        Returns:
            str | None: Action string if drone moved or waited, else None
        """
        if self.wait_turns > 0:
            self.wait_turns -= 1
            return str(self)

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
        return None


class Hub:
    """Represent a hub in the map graph.
    """

    def __init__(
        self,
        name: str,
        zone: str,
        color: str,
        max_drones: int,
        coords: tuple[int, int],
        is_extremity: bool
    ):
        """Build hub object.

        Args:
            name (str): Hub name
            zone (str): Hub zone type
            color (str): Hub display color name
            max_drones (int): Max drones allowed inside the hub
            coords (tuple[int, int]): Hub coordinates on map
            is_extremity (bool): True for start/end hub
        """
        self.is_extremity = is_extremity
        self.name = name
        self.zone = zone
        self.color = color
        self.max_drones = max_drones
        self.coords = coords
        self.connections: dict["Hub", Connection] = {}
        self.current_drones = 0
        self.all_drones: dict[int, Drone] = {}

    def add_connection(self, remote: "Hub", connection: Connection) -> None:
        """Attach a connection to another hub.

        Args:
            remote (Hub): Remote connected hub
            connection (Connection): Connection object to store
        """
        self.connections.update({remote: connection})

    def __str__(self) -> str:
        """Return verbose hub description.

        Returns:
            str: Human-readable summary of the hub
        """
        connections = ", ".join([hub.name for hub in self.connections.keys()])
        return (
            f"Hub name: {self.name}, "
            f"Zone: ({self.zone}), "
            f"Connections: [{connections}]"
            f"Drones: {self.current_drones}"
        )

    def can_receive_drone(self) -> bool:
        """Check if this hub can accept an incoming drone.

        Returns:
            bool: True if a drone can enter the hub
        """
        if self.is_extremity:
            return True
        return self.current_drones < self.max_drones


class PathFinding:
    """Compute paths and simulate all drone movements.
    """

    def __init__(self, map_data: dict[str, Any]):
        """Build pathfinding context from parsed map data.

        Args:
            map_data (dict[str, Any]): Validated map content
        """
        self.distance = {
            "normal": 1.0,
            "blocked": -1.0,
            "restricted": 2.0,
            "priority": 0.5,
        }

        self.hubs: dict[str, Hub] = {
            hub["name"]: self._init_hub(hub, False) for hub in map_data["hubs"]
        }

        self.nb_drones = map_data["nb_drones"]
        self.start_hub = self._init_hub(map_data["start_hub"], True)
        self.end_hub = self._init_hub(map_data["end_hub"], True)

        self.all_hubs: dict[str, Hub] = {
            hub.name: hub for hub in (
                [self.start_hub] + list(self.hubs.values()) + [self.end_hub])}
        self._init_connections(map_data["connections"], self.all_hubs)

        self.drones: dict[int, Drone] = {
            id: Drone(
                id=id,
                start_hub=self.start_hub,
                pathfinding=self
            )
            for id in range(1, map_data["nb_drones"] + 1)
        }

        for drone in self.drones.values():
            self.start_hub.all_drones.update({drone.id: drone})

        self.output, self.all_data, self.turn = self._start_simulation()

    def _init_hub(self, hub: dict[str, Any], is_extremity: bool) -> Hub:
        """Create a hub instance from map payload.

        Args:
            hub (dict[str, Any]): Hub payload
            is_extremity (bool): True when hub is start or end

        Returns:
            Hub: Initialized hub object
        """
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
        connections: list[dict[str, Any]],
        all_hubs: dict[str, Hub]
    ) -> None:
        """Create bidirectional links between hubs.

        Args:
            connections (list[dict[str, Any]]): Connections payload
            all_hubs (dict[str, Hub]): Indexed hubs by name
        """
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
        """Find cheapest path using Dijkstra-like traversal.

        Args:
            start (Hub): Start hub
            end (Hub): Destination hub
            occupancy (dict[str, int] | None): Planned hub occupancy map

        Returns:
            list[Hub]: Ordered hubs to reach destination (or best reachable
                fallback), excluding start
        """
        if occupancy is None:
            occupancy = {}

        heap = [(0.0, start.name)]
        costs: dict[str, float] = {start.name: 0.0}
        prev: dict[str, str | None] = {start.name: None}

        def build_path(target_name: str) -> list["Hub"]:
            path: list[Hub] = []
            cursor: str | None = target_name
            while cursor is not None:
                path.append(self.all_hubs[cursor])
                cursor = prev[cursor]
            path.reverse()
            return path[1:]

        while heap:
            cost, name = heapq.heappop(heap)

            if cost > costs.get(name, float("inf")):
                continue

            if name == end.name:
                return build_path(name)

            current = self.all_hubs[name]
            for next_hub in current.connections:
                connection_cost = self.distance.get(
                    next_hub.zone, float("inf"))

                if connection_cost < 0:
                    continue

                if not next_hub.is_extremity:
                    alloc = occupancy.get(next_hub.name, 0)
                    if alloc >= next_hub.max_drones:
                        connection_cost += (
                            alloc - next_hub.max_drones + 1) * 0.02

                new_cost = cost + connection_cost
                if new_cost < costs.get(next_hub.name, float("inf")):
                    costs[next_hub.name] = new_cost
                    prev[next_hub.name] = name
                    heapq.heappush(heap, (new_cost, next_hub.name))

        reachable_names = [name for name in costs if name != start.name]
        if not reachable_names:
            return []

        end_x, end_y = end.coords
        fallback_name = min(
            reachable_names,
            key=lambda hub_name: (
                abs(self.all_hubs[hub_name].coords[0] - end_x)
                + abs(self.all_hubs[hub_name].coords[1] - end_y),
                costs[hub_name],
            ),
        )
        return build_path(fallback_name)

        return []

    def _start_simulation(self) -> Any:
        """Run the full turn-by-turn drone simulation.

        Returns:
            Any: Tuple of actions per turn, snapshots, and total turn count
        """
        actions: list[str] = []

        occupancy: dict[str, int] = {name: 0 for name in self.all_hubs}
        for drone in self.drones.values():
            path = self._find_path(self.start_hub, self.end_hub, occupancy)
            drone.path_follow = path
            for hub in path:
                if not hub.is_extremity:
                    occupancy[hub.name] += 1

        turn = 0
        max_turns = 10000
        all_data: dict[int, dict[int, dict[str, Any]]] = {}
        while (
            turn < max_turns
            and any(
                not drone.finish and drone.current_hub != self.end_hub
                for drone in self.drones.values()
            )
        ):
            turn_actions = []
            moved_this_turn = False
            turn += 1
            all_data[turn] = {}

            for drone in self.drones.values():
                if not drone.finish:
                    last_hub = drone.current_hub
                    current_turn = drone.execute_turn()

                    if drone.current_hub != last_hub:
                        moved_this_turn = True

                    if current_turn is not None:
                        try:
                            last_hub.all_drones.pop(drone.id)
                        except KeyError:
                            pass

                        drone.current_hub.all_drones.update({drone.id: drone})
                        turn_actions.append(current_turn)

                all_data[turn][drone.id] = {
                    "hub": drone.current_hub.name,
                    "coords": self.all_hubs[drone.current_hub.name].coords,
                }
            actions.append(" ".join(turn_actions))

            still_waiting = any(
                (not drone.finish)
                and drone.current_hub != self.end_hub
                and drone.wait_turns > 0
                for drone in self.drones.values()
            )
            if not moved_this_turn and not still_waiting:
                if not turn_actions:
                    actions.pop()
                    all_data.pop(turn, None)
                    turn -= 1
                for drone in self.drones.values():
                    if not drone.finish and drone.current_hub != self.end_hub:
                        drone.finish = True
                break

        return actions, all_data, turn
