#!/usr/bin/env python3
"""
Generate worlds/warehouse.sdf, a slightly messy 20 x 15 m warehouse.

It has rooms, two centre walls and hangout areas.

    python3 tools/gen_warehouse.py        # rewrites ../worlds/warehouse.sdf

Layout (top view, metres; the robot spawns at the origin on the main walkway):

  y=7.5 +-----------+--------------------------------+----------+
        |  storage  | ========= rack N1 (wall) ===== |  office  |
        |   room    |  ======== rack N2 ========     D          |
        +----D------+  ======== rack N3 ========     +----------+ y=3.5
        | chill     |                                | meeting  |
        | corner  ==+====D====== centre wall ===D==  D  room    |
        |                                            +----------+ y=0
        |  ========= main walkway (spawn 0,0) =======D kitchen- |
        |                     |                      |  ette    |
        | |  |  |  |  racks   |  lounge    ping-pong +----------+ y=-3.5
        | S1 S2 S3 S4         |  (sofas)             D workshop |
        |        pallets      | staging (pallets)    D (roller) |
 y=-7.5 +---------------------+----------------------+----------+
      x=-10                 x=-1.2                  x=6        x=10

Robot scale: footprint 0.32 x 0.30 m, lidar plane ~0.15 m above the floor.
Racks have a solid bottom deck (the lidar sees a continuous edge); tables
stand on legs; aisles and doorways are >= 0.9 m; clutter stays off the paths.
"""

import math
import os
import random

WALL_T = 0.15
WALL_H = 1.5          # lowered so the Gazebo camera can see inside

CONCRETE = (0.62, 0.62, 0.60)
WALL = (0.80, 0.80, 0.78)
RACK_BLUE = (0.15, 0.30, 0.65)
RACK_ORANGE = (0.90, 0.45, 0.10)
PALLET = (0.70, 0.55, 0.35)
CARDBOARD = (0.72, 0.56, 0.36)
CARDBOARD_DARK = (0.60, 0.45, 0.28)
BARREL_BLUE = (0.10, 0.25, 0.60)
BARREL_RED = (0.65, 0.12, 0.10)
CONE = (0.95, 0.40, 0.05)
YELLOW = (0.95, 0.80, 0.10)
GREY = (0.40, 0.40, 0.42)
DESK = (0.55, 0.40, 0.25)
WHITE = (0.95, 0.95, 0.95)
FABRIC = (0.45, 0.47, 0.52)
LEAF = (0.20, 0.50, 0.22)

rng = random.Random(7)          # fixed seed: same "mess" every time
_models = []


def _mat(rgb):
    r, g, b = rgb
    return (f'<material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse>'
            f'<specular>0.1 0.1 0.1 1</specular></material>')


def _box(sx, sy, sz):
    return f'<box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box>'


def _cyl(r, h):
    return f'<cylinder><radius>{r:.3f}</radius><length>{h:.3f}</length></cylinder>'


def model(name, x, y, yaw, parts, collide=True):
    """parts: [(geometry, (dx, dy, z), rgb)] relative to the model pose (x, y, yaw)."""
    body = []
    for i, (geom, (dx, dy, z), rgb) in enumerate(parts):
        pose = f'<pose>{dx:.3f} {dy:.3f} {z:.3f} 0 0 0</pose>'
        if collide:
            body.append(f'<collision name="c{i}">{pose}<geometry>{geom}</geometry></collision>')
        body.append(f'<visual name="v{i}">{pose}<geometry>{geom}</geometry>{_mat(rgb)}</visual>')
    _models.append(f'    <model name="{name}"><static>true</static>'
                   f'<pose>{x:.3f} {y:.3f} 0 0 0 {yaw:.4f}</pose><link name="link">\n      '
                   + '\n      '.join(body) + '\n    </link></model>')


def box(name, x, y, sx, sy, sz, rgb, yaw=0.0, z0=0.0):
    model(name, x, y, yaw, [(_box(sx, sy, sz), (0, 0, z0 + sz / 2), rgb)])


def wall(name, x0, y0, x1, y1, doors=()):
    """Axis-aligned wall with door gaps [(a, b)] along it."""
    horiz = y0 == y1
    a, b = (x0, x1) if horiz else (y0, y1)
    segs, start = [], a
    for d0, d1 in sorted(doors):
        segs.append((start, d0))
        start = d1
    segs.append((start, b))
    for i, (s0, s1) in enumerate(segs):
        if s1 - s0 < 1e-6:
            continue
        if horiz:
            # overlap the corners at the wall's own ends, but never into a doorway
            e0 = s0 - WALL_T / 2 if s0 == a else s0
            e1 = s1 + WALL_T / 2 if s1 == b else s1
            box(f'{name}_{i}', (e0 + e1) / 2, y0, e1 - e0, WALL_T, WALL_H, WALL)
        else:
            box(f'{name}_{i}', x0, (s0 + s1) / 2, WALL_T, s1 - s0, WALL_H, WALL)


def rack(name, x0, y0, x1, y1, color=RACK_BLUE, levels=(0.0, 0.55, 1.05), fill=0.6):
    """Pallet rack: solid bottom deck + upright posts + shelves, partly filled with boxes."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lx, ly = x1 - x0, y1 - y0
    along_x = lx >= ly
    length, depth = (lx, ly) if along_x else (ly, lx)
    parts = []
    # posts every ~1.4 m
    n_bays = max(1, round(length / 1.4))
    for k in range(n_bays + 1):
        t = -length / 2 + k * length / n_bays
        for s in (-depth / 2 + 0.04, depth / 2 - 0.04):
            px, py = (t, s) if along_x else (s, t)
            post_h = levels[-1] + 0.35
            parts.append((_box(0.07, 0.07, post_h), (px, py, post_h / 2), color))
    # shelves (bottom one is a solid deck from the floor up, so the lidar sees it)
    for lv in levels:
        h = 0.18 if lv == 0.0 else 0.05
        sx, sy = (length, depth) if along_x else (depth, length)
        parts.append((_box(sx, sy, h), (0, 0, lv + h / 2), color if lv else PALLET))
    # boxes on the shelves (messy: random sizes, offsets, gaps)
    for lv in levels:
        base = lv + (0.18 if lv == 0.0 else 0.05)
        t = -length / 2 + 0.1
        while t < length / 2 - 0.35:
            w = rng.uniform(0.3, 0.6)
            if rng.random() < fill and t + w < length / 2 - 0.05:
                h = rng.uniform(0.2, 0.4)
                d = depth * rng.uniform(0.6, 0.85)
                off = rng.uniform(-0.05, 0.05)
                bx, by = (t + w / 2, off) if along_x else (off, t + w / 2)
                bsx, bsy = (w, d) if along_x else (d, w)
                parts.append((_box(bsx, bsy, h), (bx, by, base + h / 2),
                              rng.choice((CARDBOARD, CARDBOARD_DARK))))
            t += w + rng.uniform(0.03, 0.15)
    model(name, cx, cy, 0.0, parts)


def pallet_stack(name, x, y, yaw, layers=2):
    """Pallet with a few boxes on it, slightly askew."""
    parts = [(_box(1.0, 0.8, 0.14), (0, 0, 0.07), PALLET)]
    z = 0.14
    for _ in range(layers):
        h = rng.uniform(0.25, 0.35)
        for dx in (-0.25, 0.25):
            for dy in (-0.2, 0.2):
                if rng.random() < 0.8:
                    parts.append((_box(0.45, 0.36, h),
                                  (dx + rng.uniform(-0.03, 0.03),
                                   dy + rng.uniform(-0.03, 0.03), z + h / 2),
                                  rng.choice((CARDBOARD, CARDBOARD_DARK))))
        z += h
    model(name, x, y, yaw, parts)


def barrel(name, x, y, rgb):
    model(name, x, y, 0.0, [(_cyl(0.29, 0.88), (0, 0, 0.44), rgb)])


def cone(name, x, y):
    model(name, x, y, 0.0, [(_box(0.36, 0.36, 0.03), (0, 0, 0.015), BARREL_RED),
                            (_cyl(0.11, 0.5), (0, 0, 0.28), CONE)])


def legs_table(name, x, y, sx, sy, h, rgb, yaw=0.0, leg=0.05):
    """Table on four legs (the lidar sees the legs, the robot fits underneath)."""
    dx, dy = sx / 2 - leg, sy / 2 - leg
    parts = [(_box(sx, sy, 0.04), (0, 0, h - 0.02), rgb)]
    for lx in (-dx, dx):
        for ly in (-dy, dy):
            parts.append((_box(leg, leg, h - 0.04), (lx, ly, (h - 0.04) / 2), rgb))
    model(name, x, y, yaw, parts)


def sofa(name, x, y, yaw, length, rgb):
    """Sofa facing +y in its own frame: seat, backrest, two arms."""
    model(name, x, y, yaw, [(_box(length, 0.85, 0.42), (0, 0, 0.21), rgb),
                            (_box(length, 0.18, 0.85), (0, -0.335, 0.425), rgb),
                            (_box(0.15, 0.85, 0.62), (-length / 2 + 0.075, 0, 0.31), rgb),
                            (_box(0.15, 0.85, 0.62), (length / 2 - 0.075, 0, 0.31), rgb)])


def bean_bag(name, x, y, rgb):
    model(name, x, y, 0.0, [(_cyl(0.38, 0.45), (0, 0, 0.225), rgb)])


def cafe_table(name, x, y):
    """Round table on a single post."""
    model(name, x, y, 0.0, [(_cyl(0.25, 0.03), (0, 0, 0.015), GREY),
                            (_cyl(0.05, 0.72), (0, 0, 0.36), GREY),
                            (_cyl(0.45, 0.04), (0, 0, 0.74), DESK)])


def rug(name, x, y, sx, sy, rgb, yaw=0.0):
    model(name, x, y, yaw, [(_box(sx, sy, 0.006), (0, 0, 0.003), rgb)], collide=False)


def plant(name, x, y):
    model(name, x, y, 0.0, [(_cyl(0.18, 0.4), (0, 0, 0.2), BARREL_RED),
                            (_cyl(0.28, 0.6), (0, 0, 0.7), LEAF)])


def build():
    X0, X1, Y0, Y1 = -10.0, 10.0, -7.5, 7.5
    EAST = 6.0                       # west wall of the east rooms

    model('floor', 0, 0, 0, [(_box(X1 - X0, Y1 - Y0, 0.004), (0, 0, 0.002), CONCRETE)],
          collide=False)
    model('walkway_lines', 0, 0, 0, [(_box(15.0, 0.06, 0.005), (-2.5, -0.85, 0.003), YELLOW),
                                     (_box(15.0, 0.06, 0.005), (-2.5, 1.9, 0.003), YELLOW)],
          collide=False)

    # ================= shell =================
    wall('wall_s', X0, Y0, X1, Y0)
    wall('wall_n', X0, Y1, X1, Y1)
    wall('wall_w', X0, Y0, X0, Y1)
    wall('wall_e', X1, Y0, X1, Y1)

    # ================= centre walls =================
    # 1) partition between the racking zone and the main walkway, two doorways
    wall('centre_wall_ns', -4.5, 2.0, 4.8, 2.0, doors=[(-1.6, -0.5), (2.6, 3.7)])
    # 2) free-standing wall splitting the south half: racks (west) | hangout (east)
    wall('centre_wall_we', -1.2, -6.0, -1.2, -1.6)

    # ================= east rooms =================
    wall('east_rooms_w', EAST, Y0, EAST, Y1,
         doors=[(4.2, 5.1), (0.5, 1.4), (-1.2, -0.3), (-6.0, -4.6)])
    wall('office_s', EAST, 3.5, X1, 3.5)
    wall('meeting_s', EAST, 0.0, X1, 0.0)
    wall('kitchen_s', EAST, -3.5, X1, -3.5)

    # office (y 3.5..7.5)
    box('office_desk_1', 8.3, 7.05, 1.4, 0.65, 0.75, DESK)
    box('office_desk_2', 9.5, 5.2, 0.65, 1.4, 0.75, DESK)
    box('office_chair_1', 8.2, 6.4, 0.5, 0.5, 0.5, GREY, yaw=0.3)
    box('office_chair_2', 8.8, 5.0, 0.5, 0.5, 0.5, GREY, yaw=-0.5)
    box('office_cabinet', 6.6, 7.1, 0.9, 0.45, 1.2, GREY)
    box('office_boxes', 9.5, 3.95, 0.5, 0.4, 0.4, CARDBOARD, yaw=0.2)
    plant('office_plant', 6.5, 3.95)

    # meeting room (y 0..3.5)
    legs_table('meeting_table', 8.3, 1.75, 2.0, 1.0, 0.75, DESK)
    seats = ((7.7, 0.95), (8.9, 0.95), (7.7, 2.55), (8.9, 2.55), (9.6, 1.75))
    for i, (cx, cy) in enumerate(seats):
        box(f'meeting_chair_{i}', cx, cy, 0.45, 0.45, 0.45, GREY, yaw=0.15 * (i - 2))
    box('whiteboard', 9.88, 1.75, 0.06, 1.6, 1.0, (0.97, 0.97, 0.97), z0=0.5)

    # kitchenette (y -3.5..0)
    box('kitchen_counter', 9.6, -1.75, 0.6, 2.4, 0.9, GREY)
    box('kitchen_fridge', 9.6, -3.05, 0.7, 0.7, 1.4, (0.9, 0.9, 0.9))
    box('vending_machine', 6.55, -3.05, 0.9, 0.7, 1.4, BARREL_RED)
    cafe_table('kitchen_table', 7.9, -1.6)
    box('kitchen_stool_1', 7.4, -2.3, 0.35, 0.35, 0.45, BARREL_BLUE)
    box('kitchen_stool_2', 8.5, -2.0, 0.35, 0.35, 0.45, BARREL_BLUE)

    # workshop (y -7.5..-3.5), wide roller-door opening
    box('workbench', 9.6, -5.3, 0.7, 2.4, 0.9, DESK)
    box('tool_cabinet', 9.55, -3.95, 0.7, 0.6, 1.2, BARREL_RED)
    box('workshop_shelf', 8.0, -7.15, 2.4, 0.5, 1.3, RACK_ORANGE)
    model('engine_block', 8.0, -5.2, 0.4, [(_box(0.7, 0.5, 0.5), (0, 0, 0.25), GREY)])
    barrel('ws_barrel_1', 6.5, -7.0, BARREL_BLUE)
    barrel('ws_barrel_2', 7.15, -7.0, BARREL_RED)
    cone('ws_cone', 6.6, -3.95)

    # ================= storage room (north-west) =================
    wall('storage_e', -5.5, 4.0, -5.5, Y1)
    wall('storage_s', X0, 4.0, -5.5, 4.0, doors=[(-8.2, -7.2)])
    rack('storage_rack_n', -9.85, 6.85, -5.9, 7.35, RACK_BLUE, levels=(0.0, 0.6), fill=0.8)
    rack('storage_rack_w', -9.85, 4.4, -9.35, 6.3, RACK_ORANGE, levels=(0.0, 0.6), fill=0.8)
    box('storage_box_1', -6.6, 5.3, 0.6, 0.5, 0.5, CARDBOARD, yaw=0.4)
    box('storage_box_2', -6.0, 4.5, 0.45, 0.45, 0.4, CARDBOARD_DARK, yaw=-0.2)
    box('storage_box_3', -8.3, 5.7, 0.5, 0.4, 0.3, CARDBOARD, yaw=1.1)

    # ================= racking zone (north of the partition) =================
    rack('rack_n1', -5.0, 6.85, 5.6, 7.35, RACK_BLUE)
    rack('rack_n2', -4.3, 5.05, 5.0, 5.65, RACK_ORANGE)
    rack('rack_n3', -4.3, 3.25, 5.0, 3.85, RACK_BLUE)
    box('aisle_box', 1.5, 6.25, 0.4, 0.35, 0.3, CARDBOARD, yaw=0.6)

    # ================= chill corner (north-west of the hall, below storage) =================
    rug('chill_rug', -7.6, 1.9, 3.0, 2.2, (0.35, 0.55, 0.60))
    bean_bag('bean_bag_1', -9.2, 2.9, (0.85, 0.30, 0.25))
    bean_bag('bean_bag_2', -6.3, 2.9, (0.25, 0.55, 0.30))
    cafe_table('chill_table', -7.6, 1.6)
    box('chill_stool_1', -8.4, 1.3, 0.35, 0.35, 0.45, BARREL_BLUE)
    box('chill_stool_2', -6.8, 1.2, 0.35, 0.35, 0.45, BARREL_BLUE)
    model('arcade_machine', -9.6, 0.9, 0.0,
          [(_box(0.6, 0.7, 1.4), (0, 0, 0.7), (0.25, 0.10, 0.45))])
    plant('chill_plant', -5.2, 3.5)

    # ================= south-west racks (along y) =================
    for i, x in enumerate((-9.85, -8.0, -6.15, -4.3)):
        rack(f'rack_s{i + 1}', x, -7.35 if i == 0 else -6.9, x + 0.6, -2.4,
             RACK_BLUE if i % 2 == 0 else RACK_ORANGE)
    pallet_stack('sw_pallet', -2.4, -6.6, 0.25)
    model('sw_empty_pallets', -2.5, -3.6, -0.4, [(_box(1.0, 0.8, 0.14 * 2), (0, 0, 0.14), PALLET)])

    # ================= hangout lounge (south-east of the hall) =================
    rug('lounge_rug', 1.3, -3.1, 3.4, 2.6, (0.60, 0.25, 0.25))
    sofa('lounge_sofa_1', -0.6, -3.0, -math.pi / 2, 2.0, FABRIC)
    sofa('lounge_sofa_2', 1.2, -4.35, 0.0, 2.0, FABRIC)
    legs_table('coffee_table', 1.1, -2.95, 1.0, 0.6, 0.42, DESK)
    bean_bag('lounge_bean_1', 2.6, -2.2, (0.95, 0.75, 0.15))
    bean_bag('lounge_bean_2', 2.85, -3.5, (0.20, 0.45, 0.75))
    plant('lounge_plant_1', -0.75, -1.65)
    plant('lounge_plant_2', 2.6, -4.75)
    # ping-pong table with a net
    model('ping_pong', 4.6, -3.0, 0.0,
          [(_box(1.52, 2.74, 0.04), (0, 0, 0.74), (0.10, 0.35, 0.20)),
           (_box(1.70, 0.02, 0.15), (0, 0, 0.83), WHITE)]
          + [(_box(0.06, 0.06, 0.72), (lx, ly, 0.36), GREY)
             for lx in (-0.65, 0.65) for ly in (-1.2, 1.2)])

    # ================= staging along the south wall =================
    pallet_stack('pallet_1', 0.3, -6.85, 0.12)
    pallet_stack('pallet_2', 1.8, -6.9, -0.2, layers=1)
    pallet_stack('pallet_3', 3.3, -6.8, 0.1, layers=3)
    model('pallet_jack', 2.6, -5.7, 2.9,
          [(_box(1.1, 0.16, 0.08), (0.0, -0.2, 0.04), YELLOW),
           (_box(1.1, 0.16, 0.08), (0.0, 0.2, 0.04), YELLOW),
           (_box(0.3, 0.6, 0.35), (0.65, 0.0, 0.175), YELLOW),
           (_box(0.05, 0.05, 1.0), (0.85, 0.0, 0.6), GREY)])

    # ================= mess around the walkway =================
    box('loose_box_1', 1.6, 0.9, 0.5, 0.4, 0.35, CARDBOARD, yaw=0.5)
    box('toppled_box', 4.3, -0.3, 0.6, 0.4, 0.35, CARDBOARD_DARK, yaw=0.9)
    box('crate_stack', -9.5, -1.6, 0.5, 0.5, 0.6, CARDBOARD, yaw=0.2)
    box('stray_box', -3.4, 1.2, 0.45, 0.4, 0.3, CARDBOARD, yaw=0.7)
    barrel('barrel_1', -9.6, -0.7, BARREL_BLUE)
    barrel('barrel_2', -9.6, -0.1, BARREL_BLUE)
    barrel('barrel_3', -9.0, -0.4, BARREL_RED)
    cone('cone_1', -1.9, -1.4)
    cone('cone_2', 5.4, -5.0)
    cone('cone_3', 5.3, 1.6)
    model('bin', -4.9, 1.5, 0.0, [(_cyl(0.25, 0.8), (0, 0, 0.4), GREY)])


HEADER = """<?xml version="1.0" ?>
<!-- GENERATED by tools/gen_warehouse.py. Edit that script, not this file. -->
<sdf version="1.9">
  <world name="warehouse">
    <physics name="smooth" type="dart">
      <max_step_size>0.002</max_step_size>
      <real_time_factor>1</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
    <gravity>0 0 -9.8</gravity>
    <scene>
      <ambient>0.5 0.5 0.5 1</ambient>
      <background>0.75 0.8 0.85 1</background>
      <shadows>true</shadows>
    </scene>
    <model name="ground_plane">
      <static>true</static>
      <link name="ground_link">
        <collision name="ground_collision">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <surface>
            <friction><ode><mu>1.5</mu><mu2>1.5</mu2></ode></friction>
            <bounce><restitution_coefficient>0</restitution_coefficient></bounce>
          </surface>
        </collision>
        <visual name="ground_visual">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <material><ambient>0.5 0.55 0.48 1</ambient><diffuse>0.5 0.55 0.48 1</diffuse></material>
        </visual>
      </link>
    </model>
    <light name="sun" type="directional">
      <pose>0 0 10 0 0 0</pose>
      <cast_shadows>true</cast_shadows>
      <diffuse>0.85 0.85 0.85 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.4 0.2 -0.9</direction>
    </light>
"""

FOOTER = """
  </world>
</sdf>
"""


def main():
    build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'warehouse.sdf')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(HEADER + '\n'.join(_models) + FOOTER)
    print(f'wrote {os.path.normpath(out)} ({len(_models)} models)')


if __name__ == '__main__':
    main()
