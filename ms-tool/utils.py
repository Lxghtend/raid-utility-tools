import time
import asyncio
import threading
import pyperclip
import configparser
from wizwalker.memory import Window
from wizwalker.errors import HookNotActive
from wizwalker import ClientHandler, Client, XYZ
from wizwalker.constants import Keycode, Primitive
from wizwalker.memory.memory_objects.client_object import DynamicClientObject
from wizwalker.memory.memory_objects.enums import WindowFlags

from worlds_collide import WorldsCollideTP

excluded_drums = [
    XYZ(-3.070, -900.000, 680.000),
    XYZ(-126.960, -900.000, 680.000),
    XYZ(117.797, -900.000, 680.000),
    XYZ(-249.350, -900.000, 680.000),
    XYZ(-993.921, -900.000, 680.000),
    XYZ(-1113.587, -900.000, 680.000),
    XYZ(-1232.520, -900.000, 680.000),
    XYZ(-1351.739, -900.000, 679.999),
]

class Utils():
    def __init__(self):
        self.handler = ClientHandler()
        self.config_parser = configparser.ConfigParser()
        self.foreground_client = None

        threading.Thread(target=self.update_foreground_client, daemon=True).start()
        threading.Thread(target=lambda: asyncio.run(self.update_hooked_text()), daemon=True).start()

    def update_foreground_client(self):
        while True:
            if (client := self.handler.get_foreground_client()):
                self.foreground_client = client
            time.sleep(0.1)

    async def update_hooked_text(self):
        async def write_window_rectangle(window: Window, x1: int, y1: int, x2: int, y2: int):
            await window.write_value_to_offset(160, x1, Primitive.int32)
            await window.write_value_to_offset(164, y1, Primitive.int32)
            await window.write_value_to_offset(168, x2, Primitive.int32)
            await window.write_value_to_offset(172, y2, Primitive.int32)

        while True:
            for client in self.get_open_clients():
                try:
                    window = (await client.root_window.get_windows_with_name('txtTestRealmText'))[0]

                    await write_window_rectangle(window, 10, 146, 153, 165)

                    await window.write_maybe_text('HOOKED')
                    await window.write_flags(WindowFlags.visible)

                except (IndexError, HookNotActive):
                    pass

            await asyncio.sleep(1)

    def read_config(self) -> dict[str, bool]:
        settings = {}
        self.config_parser.read("config.ini")

        # [General]
        settings["always_on_top"] = self.config_parser.getboolean("General", "always_on_top", fallback=True)
        settings["enable_clients_tab"] = self.config_parser.getboolean("General", "enable_clients_tab", fallback=True)
        settings["use_raid_theme"] = self.config_parser.getboolean("General", "use_raid_theme", fallback=True)

        # [Keybinds]
        settings["handle_xyz_sync"] = self.config_parser.get("Keybinds", "handle_xyz_sync", fallback="F3")
        settings["toggle_speedhack"] = self.config_parser.get("Keybinds", "toggle_speedhack", fallback="F4")
        settings["toggle_freecam"] = self.config_parser.get("Keybinds", "toggle_freecam", fallback="F5")
        settings["handle_freecam_teleport"] = self.config_parser.get("Keybinds", "handle_freecam_teleport", fallback="F6")
        settings["toggle_auto_dialogue"] = self.config_parser.get("Keybinds", "toggle_auto_dialogue", fallback="F7")

        return settings

    async def is_visible_by_path(self, base_window: Window, path: list[str]):
        if window := await self.window_from_path(base_window, path):
            return await window.is_visible()
        return False

    async def window_from_path(self, base_window: Window, path: list[str]) -> Window:
        if not path:
            return base_window
        for child in await base_window.children():
            if await child.name() == path[0]:
                if found_window := await self.window_from_path(child, path[1:]):
                    return found_window
        return False

    def get_open_clients(self) -> list[Client]:
        self.handler.remove_dead_clients()

        clients = self.handler.get_new_clients()
        if not clients:
            clients = self.handler.get_ordered_clients()
        return clients

    def rename_clients(self):
        clients = self.handler.get_new_clients()
        if not clients:
            clients = self.handler.get_ordered_clients()

        for i, client in enumerate(clients, 1):
            client.title = "Client: " + str(i)

    async def activate_hooks(self, client: Client): # TODO: rework logic and make this stop getting clients from get_open_clients
        await client.activate_hooks()
        print(f"{client.title} hooks activated.")

    async def deactivate_hooks(self, client: Client): # TODO: rework logic and make this stop getting clients from get_open_clients
        hooked_window = (await client.root_window.get_windows_with_name('txtTestRealmText'))[0]
        await hooked_window.write_flags(WindowFlags.disabled)

        await client.close()
        print(f"{client.title} hooks deactivated.")

    async def handle_auto_dialogue(self, client: Client):
        try:
            print(f"{client.title} auto dialogue activated.")

            while True:
                if await self.is_visible_by_path(client.root_window, ['WorldView', 'wndDialogMain', 'btnRight']):
                    await client.send_key(Keycode.SPACEBAR)
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
                print(f"{client.title} auto dialogue deactivated.")

    async def handle_speedhack(self, client: Client):
        try:
            print(f"{client.title} speedhack activated.")

            while True:
                await client.client_object.write_speed_multiplier(400)
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            await client.client_object.write_speed_multiplier(1)
            print(f"{client.title} speedhack deactivated.")

    async def handle_freecam(self):
        client = self.foreground_client
        if client:
            try:
                while True:
                    if not await client.game_client.is_freecam():
                        await client.camera_freecam()
                        print(f"[TOGGLE] Freecam started.")

                    await asyncio.sleep(0)

            except asyncio.CancelledError:
                camera = await client.game_client.free_camera_controller()
                camera_pos = await camera.position()

                await client.camera_elastic()
                # print(f"[TOGGLE] Freecam cancelled.")

                return camera_pos

    async def freecam_teleport(self, camera_pos: XYZ):
        client = self.foreground_client
        if client:
            await client.teleport(camera_pos, wait_on_inuse=True, purge_on_after_unuser_fixer=True)
            print(f"{client.title} teleported to freecam position.")

    async def xyz_sync(self):
        client = self.foreground_client
        if client:
            client_position = await client.body.position()

            for teleporting_client in self.handler.get_ordered_clients():
                if not teleporting_client is client:
                    await teleporting_client.teleport(client_position)

    async def copy_position(self):
        client = self.foreground_client
        if client:
            current_pos = await client.body.position()

            print(f"{client.title} copied current position at {current_pos}.")
            pyperclip.copy(f'XYZ({current_pos.x}, {current_pos.y}, {current_pos.z})')

    async def handle_basic_teleport(self, location_x: float, location_y: float, location_z: float, yaw: float = None):
        client = self.foreground_client
        if client:
            await client.teleport(XYZ(location_x, location_y, location_z), yaw)

    async def entity_teleport(self, entity_name: str):
        client = self.foreground_client
        if client:
            entity = await client.get_base_entities_with_name(entity_name)
            if not entity:
                print(f"{client.title} did not find {entity_name}")
                return

            await WorldsCollideTP(client, await entity[0].location())
            print(f"{client.title} teleported to {entity_name}.")

    async def grab_item(self, entity_name: str):
        client = self.foreground_client
        if client:
            original_location = await client.body.position()

            item = await client.get_base_entities_with_name(entity_name)

            if not item:
                print(f"{client.title} did not find {entity_name}.")
                return

            item_position = await item[0].location()

            await WorldsCollideTP(client, item_position)
            await asyncio.sleep(0.1)

            if await client.body.position() == original_location:
                return

            while not await self.is_visible_by_path(client.root_window, ['WorldView', 'NPCRangeWin', 'wndTitleBackground']):
                if await client.body.position() == original_location:
                    break
                await asyncio.sleep(0.1)

            while True:
                if not await self.is_visible_by_path(client.root_window, ['WorldView', 'NPCRangeWin', 'wndTitleBackground']):
                    break
                await client.send_key(Keycode.X, 0.1)
                await asyncio.sleep(0.1)

            if await client.body.position() != original_location:
                await client.teleport(original_location)

            print(f"{client.title} grabbed {entity_name}.")



    async def get_wisps(self) -> list[list[str, XYZ, DynamicClientObject]]:

        # Yoinked shamelessly from Deimos
        def trunc(self, f, n):
            if f > 0:
                return "%.*f" % (n, (f - 0.5*10**-n))
            elif f == 0:
                return "%.*f" % (n, f)
            elif f < 0:
                return "%.*f" % (n, (f + 0.5*10**-n))

        client = self.foreground_client
        if client:
            entity_list = await client.get_base_entities_with_name("Raid_MS_Shadow_Wisp_01")
            if not entity_list:
                print(f"{client.title} did not find wisps")
                return

            wisp_data = []
            for i, wisp in enumerate(entity_list):
                wisp_pos = await wisp.location()

                wisp_pos.x = self.trunc(wisp_pos.x, 0)
                wisp_pos.y = self.trunc(wisp_pos.y, 0)
                wisp_pos.z = self.trunc(wisp_pos.z, 0)

                info = list[f"Wisp {i+1}", wisp_pos, wisp]
                wisp_data.append(info)

            return wisp_data

    async def wisp_teleport(self, object: DynamicClientObject):
        client = self.foreground_client
        if client:
            wisp_pos = await object.location()
            if wisp_pos:
                await WorldsCollideTP(client, wisp_pos)

    async def raid_drum_teleport(self):
        client = self.foreground_client
        if client:
            drum_list = await client.get_base_entities_with_name("Raid_LightPad")

            if not drum_list:
                print(f"{client.title} did not find Raid_LightPad.")
                return

            filtered_drums = []
            for drum in drum_list:
                drum_pos = await drum.location()
                if not any(self.are_xyzs_within_threshold(drum_pos, excluded) for excluded in excluded_drums):
                    filtered_drums.append(drum)

            if len(filtered_drums) > 0:
                drum = filtered_drums[0]

                await client.teleport(await drum.location())

    async def auto_raid_drums(self):
        client = self.foreground_client
        if client:
            try:
                for i in range(8):
                    filtered_drums = []
                    while filtered_drums == []:
                        drum_list = await client.get_base_entities_with_name("Raid_LightPad")
                        for drum in drum_list:
                            drum_pos = await drum.location()
                            if not any(self.are_xyzs_within_threshold(drum_pos, excluded) for excluded in excluded_drums):
                                filtered_drums.append(drum)
                        await asyncio.sleep(0.1)

                    if filtered_drums != []:
                        target_drum = filtered_drums[0]

                        target_drum_gid = await target_drum.global_id_full()

                        await client.teleport(await drum.location())

                        while True:
                            current_drums = await client.get_base_entities_with_name("Raid_LightPad")
                            current_drum_gids = [await drum.global_id_full() for drum in current_drums]

                            if target_drum_gid not in current_drum_gids:
                                break
                            await asyncio.sleep(0.1)

                        print(f"{client.title} activated drum {i + 1}.")

                print(f"[AUTO DRUMS] completed drums.")

            except asyncio.CancelledError:
                print(f"[AUTO DRUMS] cancelled at drum #{i + 1}.")
