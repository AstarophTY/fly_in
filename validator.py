from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Literal


class HubMetadata(BaseModel):
    max_drones: int = Field(ge=1, default=1)
    type: Literal[
        "normal",
        "blocked",
        "restricted",
        "priority"
    ] = Field(default="normal")
    color: Literal[
        "green",
        "yellow",
        "red",
        "blue",
        "gray",
        "purple",
        "black",
        "brown",
        "orange",
        "maroon"
        "gold",
        "darkred",
        "crimson",
        "cyan"
    ] = Field(default=None)


class Hub(BaseModel):
    name: str = Field(min_length=1)
    coords: tuple[int, int]
    metadata: HubMetadata

    @field_validator('metadata', mode='before')
    @classmethod
    def default_metadata(cls, v: Any) -> Any:
        return v if v is not None else {}


class ConnectionMetadata(BaseModel):
    max_link_capacity: int = Field(default=1, ge=1)


class Connection(BaseModel):
    zone_a: str = Field(min_length=1)
    zone_b: str = Field(min_length=1)
    metadata: ConnectionMetadata

    @field_validator('metadata', mode='before')
    @classmethod
    def default_metadata(cls, v: Any) -> Any:
        return v if v is not None else {}


class ParsingValidator(BaseModel):
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    end_hub: Hub
    hubs: list[Hub] = Field(default=[])
    connections: list[Connection] = Field(default=[])

    @model_validator(mode='after')
    def validator(self) -> "ParsingValidator":
        all_hubs = [self.start_hub, self.end_hub] + self.hubs
        hubs_names = [hub.name for hub in all_hubs]
        hubs_coords = [hub.coords for hub in all_hubs]

        if len(hubs_names) != len(set(hubs_names)):
            raise ValueError("You can't have two hub with the same name")

        if len(hubs_coords) != len(set(hubs_coords)):
            raise ValueError("You can't have two hub on the same coords")

        for connection in self.connections:
            if (connection.zone_a not in hubs_names or
                    connection.zone_b not in hubs_names):
                raise ValueError(
                    "Invalid connection: "
                    f"{connection.zone_a}-{connection.zone_b}"
                )

        conn_tuples = [
            tuple(
                sorted(
                    [c.zone_a, c.zone_b]
                )
            ) for c in self.connections
        ]

        if len(conn_tuples) != len(set(conn_tuples)):
            raise ValueError(
                "Duplicate connections detected"
                "(ex: a-b et b-a)."
            )
        return self
