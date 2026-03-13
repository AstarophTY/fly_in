from math import sin
from typing import Any
import ursina  # type: ignore[import-untyped]
from pathfinding import PathFinding
from panda3d.core import loadPrcFileData  # type: ignore[import-untyped]
import builtins


MODEL = {
    "normal": "models/Cube_Default.gltf",
    "blocked": "models/Cube_Spikes.gltf",
    "restricted": "models/Cube_Crate.gltf",
    "priority": "models/Cube_Bricks.gltf",
}


class InputRelay(ursina.Entity):
    """Relay Ursina input/update callbacks to Graphics.
    """

    def __init__(self, graphics: "Graphics") -> None:
        """Build relay entity.

        Args:
            graphics (Graphics): Graphics instance to forward events to
        """
        super().__init__()
        self.graphics = graphics

    def input(self, key: str) -> None:
        """Forward key event to graphics handler.

        Args:
            key (str): Ursina key name
        """
        self.graphics._on_input(key)

    def update(self) -> None:
        """Forward frame update to graphics handler.
        """
        self.graphics._on_update()


class Graphics:
    """Render map, drones and HUD using Ursina.
    """

    def __init__(self, pathfinding: "PathFinding") -> None:
        """Build and start the visualization app.

        Args:
            pathfinding (PathFinding): Simulation data to render
        """
        self.pathfinding = pathfinding
        self.grid_step = 4
        self.ground_step = 2
        self.ground_padding = 1
        self.turn = 0
        self.max_turn = pathfinding.turn
        self.float_time = 0.0
        self.float_amplitude = 0.15
        self.float_speed = 2.8
        self.move_duration = 0.28

        loadPrcFileData('', 'notify-level fatal')
        loadPrcFileData('', 'notify-level-pnmimage error')
        loadPrcFileData('', 'notify-level-display error')
        builtins.print = lambda *args, **kwargs: None

        self.app = ursina.Ursina(
            show_ursina_splash=False,
            development_mode=False
        )

        ursina.window.color = ursina.color.azure
        self.sky = ursina.Sky(color=ursina.color.azure)
        ursina.AmbientLight(intensity=0.5)
        self.sun = ursina.DirectionalLight()
        self.sun.look_at(ursina.Vec3(1, -1, 1))
        self.cam = ursina.EditorCamera()
        self.robots: dict[int, Any] = {}
        self.robot_targets: dict[int, tuple[float, float, float]] = {}
        self.hub_entities: dict[str, Any] = {}
        self.hub_entities_set: set[Any] = set()
        self.links: list[Any] = []
        self.links_visible = False
        self.hub_color_mode = False
        self.minimap_drones: dict[int, Any] = {}
        self.minimap_hub_dots: dict[str, Any] = {}
        self.hub_drone_counts: dict[str, int] = {}
        self._last_hovered_hub: Any | None = None
        self._last_hover_text = ""

        self.hud_panel = ursina.Entity(
            parent=ursina.camera.ui,
            model='quad',
            scale=(0.3, 0.1),
            position=(-0.7, 0.40),
            color=ursina.color.rgba32(30, 30, 30, 120),
            enabled=False
        )

        self.hud_bg = ursina.Entity(
            parent=self.hud_panel,
            model='quad',
            scale=(0.98, 0.97),
            z=-0.01,
            color=ursina.color.rgba32(255, 255, 255, 120)
        )

        self.hub_tooltip_text = ursina.Text(
            parent=self.hud_panel,
            text="STATUS: IDLE",
            font="models/Minecraft.ttf",
            origin=(-0.5, 0.5),
            x=-0.46,
            y=0.45,
            scale=(2.6, 7.5),
            wordwrap=15,
            color=ursina.color.rgba32(200, 200, 200, 255)
        )

        self._create_struct()
        self._create_ground()
        self._create_hubs()
        self._create_links()
        self._create_robots()
        self._create_minimap()
        self._apply_turn(0)
        self._set_top_view()
        self.input_relay = InputRelay(self)

        self.app.run()

    def _create_struct(self) -> None:
        """Create start and end towers in the scene.
        """
        for hub in [self.pathfinding.start_hub, self.pathfinding.end_hub]:
            x, y, z = self._to_world(hub.coords, -1)
            ursina.Entity(
                model="models/Tower.gltf",
                x=x,
                y=y,
                z=z,
                scale=(0.5, 0.5, 0.5),
                rotation_y=(90.0 if hub.name == self.pathfinding.end_hub.name
                            else -90.0),
                collider="box",
            )

    def _set_top_view(self) -> None:
        """Configure orthographic top camera framing all hubs.
        """
        hub_coords = [hub.coords for hub in self.pathfinding.all_hubs.values()]
        if not hub_coords:
            return

        min_x = min(coord[0] for coord in hub_coords)
        max_x = max(coord[0] for coord in hub_coords)
        min_z = min(coord[1] for coord in hub_coords)
        max_z = max(coord[1] for coord in hub_coords)

        center_x = ((min_x + max_x) / 2) * self.grid_step
        center_z = ((min_z + max_z) / 2) * self.grid_step
        span_x = (max_x - min_x + 2) * self.grid_step
        span_z = (max_z - min_z + 2) * self.grid_step
        visible_span = max(span_x, span_z)

        self.cam.enabled = False
        ursina.camera.orthographic = True
        ursina.camera.fov = max(16, visible_span * 1.2)
        ursina.camera.position = (center_x, 40, center_z)
        ursina.camera.rotation = (90, 0, 0)

    def _to_world(
        self,
        coords: tuple[int, int],
        y: float
    ) -> tuple[float, float, float]:
        """Convert map coordinates to world coordinates.

        Args:
            coords (tuple[int, int]): Grid coordinates (x, z)
            y (float): Y axis value

        Returns:
            tuple[float, float, float]: World-space position
        """
        x, z = coords
        return (x * self.grid_step, y, z * self.grid_step)

    def _to_ground_world(
        self,
        x: int,
        z: int,
        y: float
    ) -> tuple[float, float, float]:
        """Build world tuple for ground block placement.

        Args:
            x (int): World x
            z (int): World z
            y (float): World y

        Returns:
            tuple[float, float, float]: World-space position
        """
        return (x, y, z)

    def _create_hubs(self) -> None:
        """Spawn hub entities and cache related metadata.
        """
        for hub in self.pathfinding.all_hubs.values():
            x, y, z = self._to_world(hub.coords, -1)
            hub_entity = ursina.Entity(
                model=MODEL.get(hub.zone, MODEL["normal"]),
                x=x,
                y=y,
                z=z,
                collider="box",
            )
            hub_entity.hub_name = hub.name
            hub_entity.hub_zone = hub.zone
            hub_entity.hub_max = hub.max_drones
            hub_entity.hub_coords = hub.coords
            hub_entity.hub_color = hub.color
            hub_entity.default_color = hub_entity.color
            self.hub_entities[hub.name] = hub_entity
            self.hub_entities_set.add(hub_entity)

    def _resolve_color(self, color_name: Any) -> Any:
        """Resolve a hub color name to a Ursina color.

        Args:
            color_name (Any): Color name to resolve

        Returns:
            Any: Ursina color value
        """
        if isinstance(color_name, str) and hasattr(ursina.color, color_name):
            return getattr(ursina.color, color_name)
        return ursina.color.white

    def _toggle_hub_colors(self) -> None:
        """Toggle hub display between default and metadata colors.
        """
        self.hub_color_mode = not self.hub_color_mode

        for hub_entity in self.hub_entities.values():
            if self.hub_color_mode:
                hub_entity.color = self._resolve_color(hub_entity.hub_color)
            else:
                hub_entity.color = hub_entity.default_color

    def _create_ground(self) -> None:
        """Generate grass blocks around all hubs.
        """
        hub_coords = {hub.coords for hub in self.pathfinding.all_hubs.values()}
        if not hub_coords:
            return

        min_hub_x = min(coord[0] for coord in hub_coords) - self.ground_padding
        max_hub_x = max(coord[0] for coord in hub_coords) + self.ground_padding
        min_hub_z = min(coord[1] for coord in hub_coords) - self.ground_padding
        max_hub_z = max(coord[1] for coord in hub_coords) + self.ground_padding

        min_world_x = min_hub_x * self.grid_step
        max_world_x = max_hub_x * self.grid_step
        min_world_z = min_hub_z * self.grid_step
        max_world_z = max_hub_z * self.grid_step

        for world_x in range(min_world_x, max_world_x + 1, self.ground_step):
            for world_z in range(
                min_world_z,
                max_world_z + 1,
                self.ground_step,
            ):
                x, y, z = self._to_ground_world(world_x, world_z, -1)
                ursina.Entity(
                    model="models/Cube_Grass_Single.gltf",
                    x=x,
                    y=y-0.25,
                    z=z,
                )

    def _create_links(self) -> None:
        """Create link entities between connected hubs.
        """
        seen_links: set[tuple[str, str]] = set()

        for from_hub in self.pathfinding.all_hubs.values():
            for to_hub in from_hub.connections:
                if from_hub.name < to_hub.name:
                    key = (from_hub.name, to_hub.name)
                else:
                    key = (to_hub.name, from_hub.name)
                if key in seen_links:
                    continue
                seen_links.add(key)

                start = ursina.Vec3(*self._to_world(from_hub.coords, -0))
                end = ursina.Vec3(*self._to_world(to_hub.coords, -0))
                delta = end - start
                length = delta.length()

                if length == 0:
                    continue

                link = ursina.Entity(
                    model="cube",
                    color=ursina.color.gray,
                    position=(start + end) / 2,
                    scale=(0.14, 0.14, length),
                )
                link.look_at(end)
                link.enabled = self.links_visible
                self.links.append(link)

    def _create_minimap(self) -> None:
        """Create minimap panel, hub dots and drone dots.
        """
        self.minimap_panel = ursina.Entity(
            parent=ursina.camera.ui,
            model="quad",
            color=ursina.color.rgba32(25, 25, 25, 150),
            position=(0.76, 0.35),
            scale=(0.2, 0.2),
        )

        self.minimap_info = ursina.Text(
            text="",
            parent=ursina.camera.ui,
            position=(0.64, 0.225),
            scale=0.85,
            color=ursina.color.rgba32(220, 220, 220, 255),
            font="models/Minecraft.ttf",
        )

        coords = [hub.coords for hub in self.pathfinding.all_hubs.values()]
        self.map_min_x = min(c[0] for c in coords)
        self.map_max_x = max(c[0] for c in coords)
        self.map_min_z = min(c[1] for c in coords)
        self.map_max_z = max(c[1] for c in coords)

        zone_color = {
            "normal": ursina.color.rgba32(130, 190, 255, 255),
            "blocked": ursina.color.rgba32(210, 90, 90, 255),
            "restricted": ursina.color.rgba32(245, 190, 95, 255),
            "priority": ursina.color.rgba32(150, 235, 130, 255),
        }

        for hub in self.pathfinding.all_hubs.values():
            px, pz = self._to_minimap(hub.coords)
            dot = ursina.Entity(
                parent=self.minimap_panel,
                model="quad",
                color=zone_color.get(hub.zone, ursina.color.white),
                position=(px, pz),
                scale=(0.03, 0.03),
            )
            self.minimap_hub_dots[hub.name] = dot

        for drone_id in self.robots:
            dot = ursina.Entity(
                parent=self.minimap_panel,
                model="quad",
                color=ursina.color.rgba32(255, 255, 40, 255),
                position=(0, 0),
                scale=(0.02, 0.02),
            )
            self.minimap_drones[drone_id] = dot

    def _to_minimap(self, coords: tuple[int, int]) -> tuple[float, float]:
        """Convert map coordinates to minimap space.

        Args:
            coords (tuple[int, int]): Grid coordinates (x, z)

        Returns:
            tuple[float, float]: Minimap position
        """
        x, z = coords
        width = max(1, self.map_max_x - self.map_min_x)
        depth = max(1, self.map_max_z - self.map_min_z)
        norm_x = (x - self.map_min_x) / width
        norm_z = (z - self.map_min_z) / depth
        px = -0.125 + norm_x * 0.25
        pz = -0.125 + norm_z * 0.25
        return (px, pz)

    def _toggle_links(self) -> None:
        """Toggle visibility of all link entities.
        """
        self.links_visible = not self.links_visible
        for link in self.links:
            link.enabled = self.links_visible

    def _create_robots(self) -> None:
        """Spawn all drone entities and their initial targets.
        """
        for drone_id in range(1, self.pathfinding.nb_drones + 1):
            self.robots[drone_id] = ursina.Entity(
                model="models/Bee.gltf",
                x=0,
                z=0,
                rotation_y=-90.0
            )
            self.robot_targets[drone_id] = (0.0, 0.0, 0.0)

    def _do_turn(self, turn: int) -> dict[int, dict[str, Any]]:
        """Return drone turn data for a requested turn.

        Args:
            turn (int): Requested turn index

        Returns:
            dict[int, dict[str, Any]]: Drone state by drone id
        """
        if turn <= 0:
            start = self.pathfinding.start_hub.coords
            return {
                drone_id: {
                    "hub": self.pathfinding.start_hub.name,
                    "coords": start,
                }
                for drone_id in self.robots
            }

        clamped_turn = max(1, min(turn, self.max_turn))
        return self.pathfinding.all_data.get(clamped_turn, {})

    def _apply_turn(self, turn: int) -> None:
        """Apply one turn snapshot to world entities and minimap.

        Args:
            turn (int): Requested turn index
        """
        self.turn = max(0, min(turn, self.max_turn))
        snapshot = self._do_turn(self.turn)
        self.hub_drone_counts = {
            hub_name: 0 for hub_name in self.pathfinding.all_hubs.keys()
        }
        for drone_data in snapshot.values():
            hub_name = drone_data["hub"]
            if hub_name in self.hub_drone_counts:
                self.hub_drone_counts[hub_name] += 1

        for drone_id, robot in self.robots.items():
            data = snapshot.get(drone_id)
            if data is None:
                continue
            x, y, z = self._to_world(data["coords"], 0)
            self.robot_targets[drone_id] = (x, y, z)
            mini_x, mini_z = self._to_minimap(data["coords"])
            self.minimap_drones[drone_id].x = mini_x
            self.minimap_drones[drone_id].y = mini_z
            robot.animate_x(
                x,
                duration=self.move_duration,
                curve=ursina.curve.linear,
            )
            robot.animate_z(
                z,
                duration=self.move_duration,
                curve=ursina.curve.linear,
            )

        self.minimap_info.text = (
            f"Tours: {self.turn}/{self.max_turn}\n"
            f"Hubs: {len(self.pathfinding.all_hubs)}  "
            f"Drones: {len(self.robots)}"
        )

    def _on_update(self) -> None:
        """Frame update: animate drones and update hover HUD.
        """
        self.float_time += ursina.time.dt

        for drone_id, robot in self.robots.items():
            target = self.robot_targets.get(drone_id)
            if target is None:
                continue

            _, base_y, _ = target
            phase = drone_id * 0.65
            robot.y = (
                base_y
                + sin(self.float_time * self.float_speed + phase)
                * self.float_amplitude
            )

        hovered = ursina.mouse.hovered_entity
        if hovered in self.hub_entities_set:
            self.hud_panel.enabled = True
            current_drones = self.hub_drone_counts.get(hovered.hub_name, 0)
            hover_text = (
                f"Hub: {hovered.hub_name}\n"
                f"Zone: {hovered.hub_zone}\n"
                f"Drones: {current_drones}/{hovered.hub_max}\n"
                f"Coords: {hovered.hub_coords}\n"
                f"Color: {hovered.hub_color}"
            )
            if (
                hovered is not self._last_hovered_hub
                or hover_text != self._last_hover_text
            ):
                self.hub_tooltip_text.text = hover_text
                self._last_hover_text = hover_text
                self._last_hovered_hub = hovered
        else:
            if self._last_hovered_hub is not None:
                self.hud_panel.enabled = False
                self.hub_tooltip_text.text = ""
                self._last_hovered_hub = None
                self._last_hover_text = ""

    def _on_input(self, key: str) -> None:
        """Handle key input for camera and simulation controls.

        Args:
            key (str): Ursina key name
        """
        if key == "c":
            self.cam.enabled = not self.cam.enabled
            if not self.cam.enabled:
                self._set_top_view()
            else:
                ursina.camera.orthographic = False
            return

        if key == "right arrow":
            self._apply_turn(self.turn + 1)
            return

        if key == "left arrow":
            self._apply_turn(self.turn - 1)
            return

        if key == "l":
            self._toggle_links()

        if key == "h":
            self._toggle_hub_colors()
