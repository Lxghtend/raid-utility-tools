import time
import asyncio
import pyperclip
import threading
import configparser
from wizwalker.constants import Keycode
from wizwalker.errors import ReadingEnumFailed
from wizwalker import ClientHandler, Client, XYZ
from wizwalker.memory import Window, MemoryReader
from wizwalker.memory.memory_objects.enums import WindowFlags
from wizwalker.memory.memory_objects.fish import FishStatusCode

from worlds_collide import WorldsCollideTP

excluded_drums = [
    XYZ(2.0806429386138916, -1375.636962890625, 1800.2769775390625),
    XYZ(-3.881438970565796, 1346.467041015625, 1800.2769775390625),
    XYZ(-1360.4449462890625, -2.781054973602295, 1800.2769775390625),
    XYZ(1345.9990234375, 7.738836765289307, 1800.2769775390625),
    XYZ(5887.60107421875, 421.2580871582031, 428.4424133300781),
    XYZ(5687.97607421875, 223.47740173339844, 429.1733093261719),
    XYZ(5682.92822265625, -44.51580047607422, 429.1733093261719),
    XYZ(5889.703125, -250.23939514160156, 429.1733093261719),
    XYZ(6156.4619140625, -254.2375030517578, 429.1733093261719),
    XYZ(6346.72607421875, -75.12811279296875, 429.1733093261719),
    XYZ(6362.3818359375, 220.32989501953125, 429.1733093261719),
    XYZ(6171.3671875, 439.0443115234375, 429.1733093261719),
    XYZ(6007.57177734375, 110.20999908447266, 432.0935974121094)
]


class Utils():
    def __init__(self):
        self.handler = ClientHandler()
        self.config_parser = configparser.ConfigParser()
        self.foreground_client = None

        threading.Thread(target=self.update_foreground_client, daemon=True).start()

    def update_foreground_client(self):
        while True:
            if (client := self.handler.get_foreground_client()):
                    self.foreground_client = client
            time.sleep(0.1)

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
    
    def are_xyzs_within_threshold(self, xyz_1 : XYZ, xyz_2 : XYZ, threshold : int = 200):
    # checks if 2 xyz's are within a rough distance threshold of each other. Not actual distance checking, but precision isn't needed for this, this exists to eliminate tiny variations in XYZ when being sent back from a failed port.
        threshold_check = [abs(abs(xyz_1.x) - abs(xyz_2.x)) < threshold, abs(abs(xyz_1.y) - abs(xyz_2.y)) < threshold, abs(abs(xyz_1.z) - abs(xyz_2.z)) < threshold]
        return all(threshold_check)

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
                await client.wait_for_zone_change()

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

    async def entity_freecam_teleport(self, entity_name: str):
        client = self.foreground_client
        if client:
            if not await client.game_client.is_freecam():
                print(f"{client.title} is not in freecam.")
                return

            entity = await client.get_base_entities_with_name(entity_name)
            if entity:
                entity = entity[0]

            camera = await client.game_client.free_camera_controller()

            if entity and camera:
                await camera.write_position(await entity.location())
                print(f"{client.title} camera teleported to {entity_name}.")

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

    async def patch_fish(self, client: Client) -> list[tuple[int, bytes]]:
        async def readbytes_writebytes(pattern:bytes, write_bytes:int) -> tuple[int, bytes]:
            add = await reader.pattern_scan(pattern, return_multiple=False)
            old_bytes = await reader.read_bytes(add, len(write_bytes))
            await reader.write_bytes(add, write_bytes)
            return (add, old_bytes)
        
        address_oldbytes = [] 
        reader = MemoryReader(client._pymem)
        
        async def scare_fish_patch():
            # scare fish patch
            num_nops = 5
            write_bytes = b"\x90" * num_nops
            pattern = rb"\xE8....\xEB.\x83\xF9\x04\x75.\xC7\x87" # E8 ?? ?? ?? ?? EB ?? 83 F9 04 75 ?? C7 87
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def bobber_submerison_rng_patch():
            # bobber submerison rng patch
            num_nops = 2
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x7D\x37\xC7\x83........\xC7\x83" # 7D 37 C7 83 ?? ?? ?? ?? ?? ?? ?? ?? C7 83
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def fish_notice_bobber_instant_patch():
            # fish notice bobber instant patch
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x82....\xC7\x83........\x8B\x93" # 0F 82 ?? ?? ?? ?? C7 83 ?? ?? ?? ?? ?? ?? ?? ?? 8B 93
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def instant_fish():
            # patch instant fish
            num_nops = 2
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x74\x63\x48\x8B\xCF\xE8....\x0F" #74 63 48 8B CF E8 ?? ?? ?? ?? 0F
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def instant_fish_2():
            # patch instant fish # 2 
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x82....\xF3\x44\x0F\x10\x0D....\x41\x0F\x2F\xC1" #0F 82 ?? ?? ?? ?? F3 44 0F 10 0D ?? ?? ?? ?? 41 0F 2F C1
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def instant_fish_3():
            # patch instant fish # 3
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x86....\xF3\x41\x0F\x5C\xF2" #0F 86 ?? ?? ?? ?? F3 41 0F 5C F2
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def instant_fish_4():
            # patch instant fish # 4
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x86....\x44\x0F\x2F\x05" #0F 86 ?? ?? ?? ?? 44 0F 2F 05
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def instant_fish_5():
            # patch instant fish # 5
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x84....\x48\x8B\x8B....\x45\x32" #0F 84 ?? ?? ?? ?? 48 8B 8B ?? ?? ?? ?? 45 32 
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))

        async def instant_fish_6():
            # patch instant fish # 6
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x84....\xF3\x0F\x10\x70\x6C\x0F\x28\xC6" #0F 84 ?? ?? ?? ?? F3 0F 10 70 6C 0F 28 C6
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))

        async def instant_fish_7():
            # patch instant fish # 7
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x86....\xF3\x0F\x10\x8B....\x0F\x28\xC1" #0F 86 ?? ?? ?? ?? F3 0F 10 8B ?? ?? ?? ?? 0F 28 C1
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))

        async def instant_fish_8():
            # patch instant fish # 8
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x86....\xF3\x0F\x10\x83....\xF3\x0F\x5C\x83" #0F 86 ?? ?? ?? ?? F3 0F 10 83 ?? ?? ?? ?? F3 0F 5C 83
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def instant_fish_9():
            # patch instant fish # 9
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x87....\xF2\x0F\x10\xB3....\xF2" #0F 87 ?? ?? ?? ?? F2 0F 10 B3 ?? ?? ?? ?? F2
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))
        
        async def skip_bobbing_patch():
            # skipping bobbing animation
            pattern = rb"\x0F\x82....\xF3\x0F\x11\x87" #0F 82 ?? ?? ?? ?? F3 0F 11 87
            write_bytes = b"\xE9\x79\x05\x00\x00\x90"
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))

        async def skip_catch_animation():
            pattern = rb"\x0F\x84....\x48..\x10\x02\x00\x00\xE8....\x84\xC0..\x48..\x78\x02\x00\x00\x00" #0F 84 ?? ?? ?? ?? 48 ?? ?? 10 02 00 00 E8 ?? ?? ?? ?? 84 C0 ?? ?? 48 ?? ?? 78 02 00 00 00
            write_bytes = b"\xE9\x88\x00\x00\x00\x90"
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))

        async def skip_struggle():
            num_nops = 6
            write_bytes = b"\x90" * num_nops
            pattern = rb"\x0F\x82....\x44..\xE4\x02\x00\x00\x48..\xC8\x02\x00\x00" # 0F 82 ?? ?? ?? ?? 44 ?? ?? E4 02 00 00 48 ?? ?? C8 02 00 00
            address_oldbytes.append(await readbytes_writebytes(pattern, write_bytes))

        patches = [
            scare_fish_patch(),
            bobber_submerison_rng_patch(),
            fish_notice_bobber_instant_patch(),
            instant_fish(),
            instant_fish_2(),
            instant_fish_3(),
            instant_fish_4(),
            instant_fish_5(),
            instant_fish_6(),
            instant_fish_7(),
            instant_fish_8(),
            instant_fish_9(),
            skip_bobbing_patch(),
            skip_catch_animation(),
            skip_struggle(),
        ]
        
        print(f"{client.title} activating fish patches...")
        await asyncio.gather(*patches)
        print(f"{client.title} completed fish patches.")

        return address_oldbytes
        
    async def reset_fish_patch(self, client: Client, address_bytes: list[tuple[int, bytes]]):
        print(f"{client.title} deactivating fish patches...")
        reader = MemoryReader(client._pymem)
        for address, oldbytes in address_bytes:
            await reader.write_bytes(address, oldbytes)
        print(f"{client.title} completed deactivating fish patches.")

    async def catch_fish(self, school: str):
        client = self.foreground_client
        if client:
            try:
                print(f"[FISH] Catching {school} fish.")
                fishing_manager = await client.game_client.fishing_manager()
                if len(await fishing_manager.fish_list()) == 0:
                    print(f"[FISH] No fish found.")
                    return
                for fish in await fishing_manager.fish_list():
                    fish_temp = await fish.template()

                    fish_is_accepted = False

                    if (await fish_temp.school_name() == school) and (await fish.is_chest() == True):
                        fish_is_accepted = True

                    if not fish_is_accepted:
                        await fish.write_status_code(FishStatusCode.escaped)

                    if fish_is_accepted:
                        fish_windows = await client.root_window.get_windows_with_name("FishingWindow")
                        while len(fish_windows) == 0:
                            async with client.mouse_handler:
                                await client.mouse_handler.click_window_with_name("OpenFishingButton")
                            fish_windows = await client.root_window.get_windows_with_name("FishingWindow")

                        fish_window: Window = fish_windows[0]
                        fish_sub_window = await fish_window.get_child_by_name("FishingSubWindow")
                        bottomframe = await fish_sub_window.get_child_by_name("BottomFrame")
                        icon1 = await bottomframe.get_child_by_name("Icon1")
                        async with client.mouse_handler:
                            await client.mouse_handler.click_window(icon1)
                        
                        is_hooked = False
                        while not is_hooked:
                            status = await fish.status_code()
                            if status == FishStatusCode.unknown2:
                                is_hooked = True
                                break
                            await asyncio.sleep(0.1)

                        if is_hooked:
                            await client.send_key(Keycode.SPACEBAR)

                        fish_failed = False
                        timeout = time.time()
                        while len(await client.root_window.get_windows_with_name("CaughtFishModalWindow")) == 0:
                            if time.time() - timeout >= 10:
                                fish_failed = True
                                break
                        
                        if fish_failed:
                            continue

                        while len(await client.root_window.get_windows_with_name("CaughtFishModalWindow")) > 0:
                            await client.send_key(Keycode.SPACEBAR)
                            await asyncio.sleep(0.1)

                        break
            
            except ReadingEnumFailed:
                pass