import asyncio
import math
from typing import List, Optional
from pathlib import Path

from loguru import logger
import numpy as np
from memobj import WindowsProcess
from wizwalker.memory import DynamicClientObject
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union, nearest_points

from wizwalker import Client, XYZ
from wizwalker.memory import Window
from typing import TypeAlias

import struct
from dataclasses import dataclass, field
from enum import Enum, Flag # We import Flag specifically for our CollisionFlag enum
from io import BytesIO
from pathlib import Path
from typing import TypeAlias
from xml.etree import ElementTree as etree
from wizwalker import Wad, Client, XYZ

Matrix3x3: TypeAlias = tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]
SimpleFace: TypeAlias = tuple[int, int, int]
SimpleVert: TypeAlias = tuple[float, float, float]
Vector3D: TypeAlias = tuple[float, float, float]
CubeVertices = tuple[Vector3D, Vector3D, Vector3D, Vector3D, Vector3D, Vector3D, Vector3D, Vector3D]


class StructIO(BytesIO):
    def read_string(self) -> str:
        length, = self.unpack("<i")
        return self.read(length).decode()

    def unpack(self, fmt: str) -> tuple:
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))


def flt(x: str) -> str:
    x, y = str(round(x, 4)).split(".")

    y = y.ljust(4, "0")

    return f"{x}.{y}"


class ProxyType(Enum):
    BOX = 0
    RAY = 1
    SPHERE = 2
    CYLINDER = 3
    TUBE = 4
    PLANE = 5
    MESH = 6
    INVALID = 7

    @property
    def xml_value(self) -> str:
        return str(self).split(".")[1].lower()

# By inheriting from 'Flag', we create an enum where members can be combined using
# bitwise operators (like OR, AND). This is perfect for representing things
# like collision layers, where an object can be in multiple categories at once.
class CollisionFlag(Flag):
    # Bitwiz/Bitshift
    OBJECT = 1 << 0        # Value is 1
    WALKABLE = 1 << 1      # Value is 2
                           # Skip 4? Or am I wrong
    HITSCAN = 1 << 3       # Value is 8
    LOCAL_PLAYER = 1 << 4  # Value is 16
    WATER = 1 << 6         # Value is 64
    CLIENT_OBJECT = 1 << 7 # Value is 128
    TRIGGER = 1 << 8       # Value is 256
    FOG = 1 << 9           # Value is 512
    GOO = 1 << 10          # Value is 1024
    FISH = 1 << 11         # Value is 2048
    MUCK = 1 << 12         # Value is 4096
    TAR = 1 << 13   # Value is 8192

    @property
    def xml_value(self) -> str:
        # Because CollisionFlag is a Flag, we can use 'in' to check if a specific
        # flag is set within a combined value. For example, the value 13379 is a
        # combination of multiple flags. If we had a variable `my_flags = CollisionFlag(13379)`,
        # the check `CollisionFlag.WALKABLE in my_flags` would be True.
        if CollisionFlag.WALKABLE in self:
            return "CT_Walkable"
        elif CollisionFlag.WATER in self:
            return "CT_Water"
        elif CollisionFlag.TRIGGER in self:
            return "CT_Trigger"
        elif CollisionFlag.OBJECT in self:
            return "CT_Object"
        elif CollisionFlag.LOCAL_PLAYER in self:
            return "CT_LocalPlayer"
        elif CollisionFlag.HITSCAN in self:
            return "CT_Hitscan"
        elif CollisionFlag.FOG in self:
            return "CT_Fog"
        elif CollisionFlag.CLIENT_OBJECT in self:
            return "CT_ClientObject"
        elif CollisionFlag.GOO in self:
            return "CT_Goo"
        elif CollisionFlag.FISH in self:
            return "CT_Fish"
        elif CollisionFlag.MUCK in self:
            return "CT_Muck"
        elif CollisionFlag.TAR in self:
            return "CT_Tar"
        else:
            return "CT_None"


# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class GeomParams:
    proxy: ProxyType

    @classmethod
    def from_stream(cls, stream: StructIO) -> "GeomParams":
        raise NotImplementedError(f"{cls.__name__}.from_stream() not implemented")

    def save_xml(self, parent):
        # stub for XML export if you ever need it
        pass

# BOX
@dataclass
class BoxGeomParams(GeomParams):
    length: float
    width:  float
    depth:  float

    @classmethod
    def from_stream(cls, stream: StructIO) -> "BoxGeomParams":
        l, w, d = stream.unpack("<fff")
        return cls(ProxyType.BOX, l, w, d)

# RAY
@dataclass
class RayGeomParams(GeomParams):
    # depending on your engine, a ray might be (origin, direction, length)
    # here we just read three floats—adjust to your real format
    origin_offset: float
    direction_offset: float
    length: float

    @classmethod
    def from_stream(cls, stream: StructIO) -> "RayGeomParams":
        o, dir_, length = stream.unpack("<fff")
        return cls(ProxyType.RAY, o, dir_, length)

# SPHERE
@dataclass
class SphereGeomParams(GeomParams):
    radius: float

    @classmethod
    def from_stream(cls, stream: StructIO) -> "SphereGeomParams":
        (r,) = stream.unpack("<f")
        return cls(ProxyType.SPHERE, r)

# CYLINDER
@dataclass
class CylinderGeomParams(GeomParams):
    radius: float
    length: float

    @classmethod
    def from_stream(cls, stream: StructIO) -> "CylinderGeomParams":
        r, l = stream.unpack("<ff")
        return cls(ProxyType.CYLINDER, r, l)

# TUBE
@dataclass
class TubeGeomParams(GeomParams):
    radius: float
    length: float

    @classmethod
    def from_stream(cls, stream: StructIO) -> "TubeGeomParams":
        r, l = stream.unpack("<ff")
        return cls(ProxyType.TUBE, r, l)

# PLANE
@dataclass
class PlaneGeomParams(GeomParams):
    normal: tuple[float, float, float]
    distance: float

    @classmethod
    def from_stream(cls, stream: StructIO) -> "PlaneGeomParams":
        nx, ny, nz, d = stream.unpack("<ffff")
        return cls(ProxyType.PLANE, (nx, ny, nz), d)

# MESH
@dataclass
class MeshGeomParams(GeomParams):
    # Mesh parameters are handled in ProxyMesh, so this carries no extra data
    @classmethod
    def from_stream(cls, stream: StructIO) -> "MeshGeomParams":
        return cls(ProxyType.MESH)

# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ProxyGeometry:
    category_flags: CollisionFlag
    collide_flag:  CollisionFlag
    name:          str          = ""
    rotation:      Matrix3x3    = (0.0,)*9
    location:      XYZ          = XYZ(0.0,0.0,0.0)
    scale:         float        = 0.0
    material:      str          = ""
    proxy:         ProxyType    = ProxyType.INVALID
    params:        GeomParams   = None

    def load(self, stream: StructIO) -> "ProxyGeometry":
        self.name     = stream.read_string()
        self.rotation = stream.unpack("<fffffffff")
        self.location = stream.unpack("<fff")
        (self.scale,) = stream.unpack("<f")
        self.material = stream.read_string()
        (ptype,)    = stream.unpack("<i")
        self.proxy   = ProxyType(ptype)

        match self.proxy:
            case ProxyType.BOX:
                self.params = BoxGeomParams.from_stream(stream)
            case ProxyType.RAY:
                self.params = RayGeomParams.from_stream(stream)
            case ProxyType.SPHERE:
                self.params = SphereGeomParams.from_stream(stream)
            case ProxyType.CYLINDER:
                self.params = CylinderGeomParams.from_stream(stream)
            case ProxyType.TUBE:
                self.params = TubeGeomParams.from_stream(stream)
            case ProxyType.PLANE:
                self.params = PlaneGeomParams.from_stream(stream)
            case ProxyType.MESH:
                self.params = MeshGeomParams.from_stream(stream)
            case _:
                raise ValueError(f"Invalid proxy type: {self.proxy}")

        return self


@dataclass
class ProxyMesh(ProxyGeometry):
    vertices: list[SimpleVert] = field(default_factory=list)
    faces: list[SimpleFace] = field(default_factory=list)
    normals: list[SimpleVert] = field(default_factory=list)

    def load(self, stream: StructIO) -> None:
        vertex_count, face_count = stream.unpack("<ii") # gives the cords of the 3d shape
        # might only need 2D not 3D for what we are doing? (NavmapTP)
        # How many points (vertices) your 3D object has.
        # How many faces (triangles, usually) your object has.
        for _ in range(vertex_count): #
            self.vertices.append(stream.unpack("<fff"))

        for _ in range(face_count):
            self.faces.append(stream.unpack("<iii"))
            self.normals.append(stream.unpack("<fff"))

        super().load(stream)

    def save_xml(self, parent: etree.Element) -> etree.Element:
        element = super().save_xml(parent)

        mesh = etree.SubElement(element, "mesh")

        vertexlist = etree.SubElement(
            mesh,
            "vertexlist",
            {"size": str(len(self.vertices))},
        )
        for x, y, z in self.vertices:
            etree.SubElement(
                vertexlist,
                "vert",
                {"x": flt(x), "y": flt(y), "z": flt(z)},
            )

        facelist = etree.SubElement(
            mesh,
            "facelist",
            {"size": str(len(self.faces))},
        )
        for a, b, c in self.faces:
            etree.SubElement(facelist, "face", {"a": str(a), "b": str(b), "c": str(c)})

        return element


@dataclass
class CollisionWorld:
    objects: list[ProxyGeometry] = field(default_factory=list)

    def load(self, raw_data: bytes) -> None:
        stream = StructIO(raw_data) # raw bytes for the whole file (mem stream)

        geometry_count, = stream.unpack("<i") # first bytes in the file is the geometry count
        for _ in range(geometry_count): # for every object in the geometry file
            # category_bits and collide_bits are for Open Dynamics Engine
            # This next line reads raw integers from the binary file. These integers
            # are the collision flags we need to interpret.
            geometry_type, category_bits, collide_bits = stream.unpack("<iII")

            # This is where the error happened. We pass an integer (like 13379) to the
            # CollisionFlag enum. The enum then checks if all the bits in that integer
            # correspond to defined flags. It failed because the bit for 8192 was set,
            # but we hadn't defined a flag for it yet.
            # Now that we have added UNKNOWN_13, this will succeed.
            #
            # For example, CollisionFlag(13379) will create a composite flag equivalent to:
            # CollisionFlag.OBJECT | WALKABLE | WATER | GOO | MUCK | UNKNOWN_13
            category = CollisionFlag(category_bits)
            collide = CollisionFlag(collide_bits)

            proxy = ProxyType(geometry_type)

            if proxy == ProxyType.MESH: # MESH is often used for floors or complex terrain
                geometry = ProxyMesh(category, collide)
            else: # Other shapes like boxes, spheres, etc.
                geometry = ProxyGeometry(category, collide)

            geometry.load(stream)
            self.objects.append(geometry)


    def save_xml(self, path: str | Path) -> etree.Element:
        world = etree.Element("world")
        for obj in self.objects:
            obj.save_xml(world)

        etree.indent(world)
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as file:
            file.write('<?xml version="1.0" encoding="utf-8" ?>\n')
            file.write(etree.tostring(world, encoding="unicode", xml_declaration=False))


async def load_wad(path: str):
    if path is not None:
        return Wad.from_game_data(path.replace("/", "-"))


async def get_collision_data(client: Client = None, zone_name: str = None) -> bytes:
    if not zone_name and client:
        zone_name = await client.zone_name()

    elif not zone_name and not client:
        raise Exception('Client and/or zone name not provided, cannot read collision.bcd.')

    wad = await load_wad(zone_name)
    collision_data = await wad.get_file("collision.bcd")

    return collision_data

def toCubeVertices(dimensions: Vector3D) -> CubeVertices:
    l, w, d = dimensions
    l /= 2
    w /= 2
    d /= 2
    return (
        (-l, -w, -d),
        (l, -w, -d),
        (l, -w, d),
        (-l, -w, d),

        (-l, w, -d),
        (l, w, -d),
        (l, w, d),
        (-l, w, d),
    )


def toMultidim(mat: Matrix3x3):
    #return (
    #    (mat[0], mat[1], mat[2]),
    #    (mat[3], mat[4], mat[5]),
    #    (mat[6], mat[7], mat[8]),
    #)
    # TODO: Should this be transposed or not? Transposed because the cubes are distorted otherwise
    return (
        (mat[0], mat[3], mat[6]),
        (mat[1], mat[4], mat[7]),
        (mat[2], mat[5], mat[8]),
    )


def transformCube(cube, location, rotation):
    tpoints = [np.dot((p,), toMultidim(rotation))[0] for p in cube]
    for p in tpoints:
        p[0] += location[0]
        p[1] += location[1]
        p[2] += location[2]
    return tpoints


async def get_window_from_path(root_window: Window, name_path: list[str]) -> Window:
    # FULL CREDIT TO SIROLAF FOR THIS FUNCTION
    async def _recurse_follow_path(window, path):
        if len(path) == 0:
            return window
        for child in await window.children():
            if await child.name() == path[0]:
                found_window = await _recurse_follow_path(child, path[1:])
                if not found_window is False:
                    return found_window

        return False

    return await _recurse_follow_path(root_window, name_path)


async def is_visible_by_path(client: Client, path: list[str]):
    # FULL CREDIT TO SIROLAF FOR THIS FUNCTION
    # checks visibility of a window from the path
    root = client.root_window
    windows = await get_window_from_path(root, path)
    if windows == False:
        return False
    elif await windows.is_visible():
        return True
    else:
        return False


async def is_free(client: Client):
    # Returns True if not in combat, loading screen, or in dialogue.
    return not any([await client.is_loading(), await client.in_battle(), await is_visible_by_path(client, ['WorldView', 'wndDialogMain', 'btnRight'])])


async def get_revision_and_zone(client: Client) -> tuple[str, str]:
    """Get the revision and zone name from the client"""
    try:
        process = WindowsProcess.from_name("WizardGraphicalClient.exe")
        wiz_bin = Path(process.executable_path).parent
        revision_file = wiz_bin / "revision.dat"

        if not revision_file.exists():
            raise FileNotFoundError(f"revision.dat not found in {wiz_bin}")

        revision = revision_file.read_text().strip()
        zone_name = await client.zone_name()
        return revision, zone_name
    except Exception as e:
        logger.error(f"Could not get revision and zone: {e}")
        return "unknown_revision", "unknown_zone"


async def _load_and_build_collision_geometry(client: Client, z_slice: float) -> tuple[CollisionWorld, List[Polygon], List[Polygon]]:
    """Loads raw collision data and builds 2D polygon shapes for static geometry."""
    raw = await get_collision_data(client)
    world = CollisionWorld()
    world.load(raw)

    coll_shapes = build_collision_shapes(world, z_slice)
    mesh_shapes = build_mesh_shapes(world, z_slice)
    return world, coll_shapes, mesh_shapes


async def _get_entity_collision_shapes(client: Client, static_body_radius: float) -> List[Polygon]:
    """
    Gets entities and approximates their collision shapes as circles.
    Uses a dynamic radius for 'CharacterBody' and a static default radius for other types.
    """
    #logger.debug("Getting dynamic entity collision shapes...")
    entity_shapes = []
    try:
        entity_list = await client.get_base_entity_list()
        for entity in entity_list:
            entity_name = await entity.object_name()
            if entity_name == "Player Object":
                continue

            actor_body = await entity.actor_body()
            if not actor_body:
                continue

            actor_type = await actor_body.read_type_name()
            entity_loc = await actor_body.position()
            entity_radius = 0.0

            if actor_type == "CharacterBody":
                entity_height = await actor_body.height()
                entity_scale = await actor_body.scale()
                entity_radius = entity_height * entity_scale * 0.5
                #logger.debug(f"Calculating radius for '{entity_name}' (CharacterBody): {entity_radius:.2f}")
            else:
                entity_radius = static_body_radius
                #logger.debug(f"Applying static radius for '{entity_name}' ({actor_type}): {entity_radius:.2f}")

            if entity_radius > 0:
                entity_shapes.append(Point(entity_loc.x, entity_loc.y).buffer(entity_radius))

    except Exception as e:
        logger.error(f"An error occurred while getting entity collision shapes: {e}", exc_info=True)

    #logger.debug(f"Generated {len(entity_shapes)} collision shapes from dynamic entities.")
    return entity_shapes


async def _perform_single_teleport_attempt(
        client: Client,
        free_area: Polygon | MultiPolygon,
        target: XYZ,
        bounds: tuple,
        base_player_radius: float,
        player_radius_offset: float
) -> bool:
    """Performs a single, non-looping teleport attempt and verifies the result."""
    epsilon = base_player_radius * 0.1
    player_radius = base_player_radius * player_radius_offset
    minx, miny, maxx, maxy = bounds

    #logger.debug(f"Performing teleport attempt with offset={player_radius_offset:.2f}, radius={player_radius:.2f}")

    if not free_area or free_area.is_empty:
        logger.error("Free area is empty, cannot calculate a safe region.")
        return False

    safe_region = free_area.buffer(-player_radius)
    if not safe_region or safe_region.is_empty:
        logger.error("Safe region is empty after buffering. Cannot find a teleport point.")
        return False

    _, pt2 = nearest_points(Point(target.x, target.y), safe_region)
    safe_pt = XYZ(pt2.x, pt2.y, target.z)
    #logger.debug(f"Calculated candidate safe_pt: {safe_pt}")

    cx = min(max(safe_pt.x, minx), maxx)
    cy = min(max(safe_pt.y, miny), maxy)
    safe_pt = XYZ(cx, cy, safe_pt.z)
    #logger.debug(f"Clamped safe_pt to instance bounds: {safe_pt}")

    start_zone_name = await client.zone_name()
    await client.teleport(safe_pt)

    #logger.debug("Waiting for server to confirm position or zone change...")
    await asyncio.sleep(0.5) #changed from 2.5 to 0.5

    new_pos = await client.body.position()
    end_zone_name = await client.zone_name()
    is_loading = await client.is_loading()

    #logger.debug(f"Position after TP and sleep: {new_pos}")
    #logger.debug(f"Zone after TP: '{end_zone_name}', Loading: {is_loading}")

    if is_loading or start_zone_name != end_zone_name:
        logger.info("Teleport successful: Zone change detected.")
        return True

    error = math.dist((new_pos.x, new_pos.y), (safe_pt.x, safe_pt.y))
    #logger.debug(f"Post-teleport 2D error={error:.2f}, Epsilon Threshold={epsilon:.2f}")

    if error < epsilon:
        logger.info("Teleport to safe point appears successful based on position error.")
        # NOTE: Removed goto() call as requested
        return True
    else:
        logger.error("Teleport to safe point FAILED. Player was likely rubber-banded.")
        return False


async def WorldsCollideTP(
        client: Client,
        target_position: XYZ,
        player_radius_offset: float = 0.5,
        static_body_radius: float = 75.0
) -> bool:
    """
    Handles teleportation to a target position by calculating a safe path around ALL collision geometry,
    including dynamic entities. Returns True if successful, False otherwise.
    """
    try:
        player_pos = await client.body.position()
        #logger.debug(f"Player position: {player_pos}")
        #logger.debug(f"Target position: {target_position}")

        world, static_coll_shapes, mesh_shapes = await _load_and_build_collision_geometry(client, target_position.z)
        entity_coll_shapes = await _get_entity_collision_shapes(client, static_body_radius)

        all_coll_shapes = static_coll_shapes + entity_coll_shapes
        #logger.debug(f"Total collision objects (static + dynamic): {len(all_coll_shapes)}")

        union_all_coll = unary_union(all_coll_shapes) if all_coll_shapes else Polygon()
        union_mesh = unary_union(mesh_shapes) if mesh_shapes else Polygon()

        free_area = union_mesh.difference(union_all_coll)

        bounds_geom = union_mesh if not union_mesh.is_empty else union_all_coll
        if bounds_geom.is_empty:
            #logger.error("No geometry (mesh or collision) found to define zone boundaries. Aborting.")
            return False
        bounds = bounds_geom.bounds
        #logger.debug(f"Instance bounds: X[{bounds[0]:.1f},{bounds[2]:.1f}]  Y[{bounds[1]:.1f},{bounds[3]:.1f}]")

        # Check for intersection using the player's actual radius
        player_height = await client.body.height()
        player_scale = await client.body.scale()
        base_player_radius = player_height * player_scale * 0.5
        player_radius = base_player_radius * player_radius_offset
        #logger.debug(f"Estimated player radius (offset applied): {player_radius:.2f}")

        player_at_target = Point(target_position.x, target_position.y).buffer(player_radius)

        if not union_all_coll.intersects(player_at_target):
            #logger.info("Target position is clear of all known collision objects. Attempting direct teleport...")
            await client.teleport(target_position)
            return True

        #logger.info("Target position intersects with collision objects. Calculating safe teleport point.")

        success = await _perform_single_teleport_attempt(
            client, free_area, target_position, bounds, base_player_radius, player_radius_offset
        )

        if success:
            #logger.info("Collision-based teleportation was successful.")
            return True
        else:
            logger.error("Collision-based teleportation failed.")
            return False

    except Exception as e:
        logger.error(f"WorldsCollideTP failed with error: {e}", exc_info=True)
        return False


def build_collision_shapes(world: CollisionWorld, z_slice: float) -> List[Polygon]:
    """Build 2D collision shapes from the collision world"""
    shapes = []

    for obj in world.objects:
        try:
            if obj.proxy == ProxyType.BOX:
                l, w, h = obj.params.length, obj.params.width, obj.params.depth
                if obj.location[2] - h / 2 <= z_slice <= obj.location[2] + h / 2:
                    verts = toCubeVertices((l, w, h))
                    world_pts = transformCube(verts, obj.location, obj.rotation)
                    pts2d = [(p[0], p[1]) for p in world_pts]
                    if len(pts2d) >= 3:
                        shapes.append(Polygon(pts2d).convex_hull)

            elif obj.proxy == ProxyType.SPHERE:
                scale_val = obj.scale if isinstance(obj.scale, (float, int)) else obj.scale[0]
                r = obj.params.radius * scale_val
                if r > 0 and abs(z_slice - obj.location[2]) <= r:
                    shapes.append(Point(obj.location[0], obj.location[1]).buffer(r))

            elif obj.proxy == ProxyType.CYLINDER:
                if isinstance(obj.scale, (float, int)):
                    scale_xy, scale_z = obj.scale, obj.scale
                else:
                    scale_xy, scale_z = obj.scale[0], obj.scale[2]

                scaled_half_length = (obj.params.length / 2) * scale_z
                scaled_radius = obj.params.radius * scale_xy * 0.125
                if scaled_radius > 0 and obj.location[2] - scaled_half_length <= z_slice <= obj.location[2] + scaled_half_length:
                    shapes.append(Point(obj.location[0], obj.location[1]).buffer(scaled_radius))

        except Exception as e:
            logger.debug(f"Error processing collision object '{obj.name}': {e}")
            continue

    return shapes


def build_mesh_shapes(world: CollisionWorld, z_slice: float) -> List[Polygon]:
    """Build 2D mesh shapes from the collision world"""
    shapes = []
    for obj in world.objects:
        if obj.proxy == ProxyType.MESH:
            pts3d = transformCube(obj.vertices, obj.location, obj.rotation)
            pts2d = [(x, y) for x, y, z in pts3d]
            if len(pts2d) >= 3:
                shapes.append(Polygon(pts2d).convex_hull)
    return shapes


async def try_navmap_fallback(client: Client, xyz: XYZ, sigma: float = 5.0) -> bool:
    """Fallback to navmap teleportation if WorldsCollideTP fails"""
    from src.teleport_math import calc_Distance, navmap_tp
    start_zone = await client.zone_name()
    start_pos = await client.body.position()

    logger.debug(f"Calling navmap_tp fallback to {xyz}")
    await navmap_tp(client, xyz)
    await asyncio.sleep(1)

    curr_pos = await client.body.position()
    curr_zone = await client.zone_name()
    moved = calc_Distance(start_pos, curr_pos) > sigma
    zone_changed = (curr_zone != start_zone)
    still_free = await is_free(client)

    logger.debug(f"Navmap result: moved={moved}, zone_changed={zone_changed}, still_free={still_free}")
    return (moved or zone_changed or not still_free)