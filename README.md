Let the drone fly
Attached to this subject, you’ll find multiple files that represent the network of drones
as the following format:
Example:
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
Interesting, right? To be more precise:
• The first line defines the number of drones using nb_drones: <number>.
• Zone definition on each line using type prefixes:
◦ start_hub: <name> <x> <y> [metadata] marks the starting zone.
◦ end_hub: <name> <x> <y> [metadata] marks the end zone.
◦ hub: <name> <x> <y> [metadata] defines a regular zone.
◦ The connection syntax forbids dashes in zone names (see below).
• All metadata is optional and enclosed in brackets [...] with default values:
◦ zone=<type> (default: normal)
◦ color=<value> (default: none)
◦ max_drones=<number> (default: 1) - Maximum drones that can occupy this
zone simultaneously
◦ Tags inside brackets can appear in any order.
• Zone types:
9
Fly-in Drones are interesting.
◦ normal – Standard zone with 1 turn movement cost (default)
◦ blocked – Inaccessible zone. Drones must not enter or pass through this zone.
Any path using it is invalid.
◦ restricted – A sensitive or dangerous zone. Movement to this zone costs 2
turns.
◦ priority – A preferred zone. Movement to this zone costs 1 turn but should
be prioritized in pathfinding.
• Colors:
◦ Colors are optional and can be used for visual representation (terminal output
or graphical display).
◦ Accepted values for color are any valid single-word strings (e.g., red, blue,
gray). There is no fixed list of allowed colors.
◦ When colors are specified, the implementation should provide visual feedback
through colored terminal output or graphical representation.
• Connections are defined using connection: <name1>-<name2> [metadata]:
◦ Define a bidirectional connection (edge) between two zones.
◦ The connection syntax forbids dashes in zone names.
◦ Optional metadata can be specified in brackets [...]:
∗ max_link_capacity=<number> (default: 1) - Maximum drones that can
traverse this connection simultaneously
• Comments start with ’#’ and are ignored.