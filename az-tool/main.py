import sys
import ctypes
import asyncio
import keyboard
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication, QLabel, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSizePolicy, QCheckBox, QDialog
from PyQt6.QtCore import QTimer, Qt,  QUrl
from PyQt6.QtGui import QIcon, QDesktopServices

from utils import Utils
from themes import Themes

class HooksTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.hooks_group_layout = QVBoxLayout()
        self.setLayout(self.hooks_group_layout)
        # --------------------------- #

        # ----- Creating Hooks Group ----- #
        self.hooks_group = QGroupBox("Hooks")
        self.hooks_tab_layout = QVBoxLayout()
        self.hooks_group.setLayout(self.hooks_tab_layout)
        # -------------------------------- #

        # ----- Rename Clients Button ----- #
        rename_clients_button = QPushButton("Rename Clients")

        rename_clients_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #rename_clients_button.setMaximumHeight(50)
        rename_clients_button.setMinimumHeight(50)

        rename_clients_button.clicked.connect(lambda: asyncio.create_task(self.rename_clients_wrapper()))

        self.hooks_tab_layout.addWidget(rename_clients_button)
        # --------------------------------- #

        self.hooks_tab_layout.addStretch() # makes rename button go to top

        # ----- Available Clients Checkboxes ----- #
        self.hooks_checkboxes = QGroupBox("Available Clients")
        self.hooks_checkboxes_layout = QVBoxLayout()

        self.client_checkboxes = []
        QTimer.singleShot(0, lambda: asyncio.create_task(self.update_client_checkboxes()))

        self.hooks_checkboxes.setLayout(self.hooks_checkboxes_layout)
        self.hooks_tab_layout.addWidget(self.hooks_checkboxes)
        # ---------------------------------------- #
        
        # ----- Creating No Clients Found Label ----- #
        self.no_clients_found_label = QLabel("No clients found.")
        self.hooks_checkboxes_layout.addWidget(self.no_clients_found_label)
        self.no_clients_found_label.hide()
        # ------------------------------------------- #

        # ----- Activate Hooks Button ----- #
        activate_hooks_button = QPushButton("Activate Hooks")

        activate_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #activate_hooks_button.setMaximumHeight(50)
        activate_hooks_button.setMinimumHeight(50)

        activate_hooks_button.clicked.connect(lambda: asyncio.create_task(self.activate_hooks_wrapper()))

        self.hooks_tab_layout.addWidget(activate_hooks_button)
        # --------------------------------- #

        # ----- Deactivate Hooks Button ----- #
        deactivate_hooks_button = QPushButton("Deactivate Hooks")

        deactivate_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #deactivate_hooks_button.setMaximumHeight(50)
        deactivate_hooks_button.setMinimumHeight(50)

        deactivate_hooks_button.clicked.connect(lambda: asyncio.create_task(self.deactivate_hooks_wrapper()))

        self.hooks_tab_layout.addWidget(deactivate_hooks_button)
        # ----------------------------------- #

        self.hooks_group_layout.addWidget(self.hooks_group)

    async def rename_clients_wrapper(self):
        print(f"[HOOKS] Rename Clients pressed.")

        self.utils.rename_clients()

    async def activate_hooks_wrapper(self):
        print("[HOOKS] Activate Hooks pressed.")

        clients_to_hook = []
        for client_checkbox in self.client_checkboxes:
            if client_checkbox.isChecked():
                client = client_checkbox.property("client")
                clients_to_hook.append(client)

        await asyncio.gather(*[(self.utils.activate_hooks(client)) for client in clients_to_hook])

        for client in clients_to_hook:
            if client.process_id not in {hooked_client.process_id for hooked_client in self.hooked_clients}:
                self.hooked_clients.append(client)

    async def deactivate_hooks_wrapper(self):
        print("[HOOKS] Deactivate Hooks pressed.")
        for client_checkbox in self.client_checkboxes:
            if client_checkbox.isChecked():
                client = client_checkbox.property("client")

                for hooked_client in self.hooked_clients:
                    if client == hooked_client:
                        self.hooked_clients.remove(client)

                await self.utils.deactivate_hooks(client)

    async def update_client_checkboxes(self):
        while True:
            clients = self.utils.get_open_clients()
            existing_processes = [client_checkbox.property("client").process_id for client_checkbox in self.client_checkboxes]

            # Remove Client Checkboxes that don't exist
            for client_checkbox in self.client_checkboxes[:]:
                if client_checkbox.property("client").process_id not in [client.process_id for client in clients]:
                    self.hooks_checkboxes_layout.removeWidget(client_checkbox)
                    client_checkbox.deleteLater()

                    self.client_checkboxes.remove(client_checkbox)

            for client_checkbox in self.client_checkboxes:
                client_process_id = client_checkbox.property("client").process_id # process id that is stored
                for client in clients:
                    if client.process_id == client_process_id:
                        if client_checkbox.text() != client.title:
                            client_checkbox.setText(client.title)
                            client_checkbox.setProperty("client", client)

            # Create Client Checkboxes
            for client in clients:
                if client.process_id not in existing_processes:
                    client_checkbox = QCheckBox(client.title)
                    client_checkbox.setProperty("client", client)

                    self.client_checkboxes.append(client_checkbox)

                    self.hooks_checkboxes_layout.addWidget(client_checkbox)
                    
            if self.client_checkboxes:
                self.no_clients_found_label.hide()

            if not self.client_checkboxes:
                self.no_clients_found_label.show()

            await asyncio.sleep(1)

class ClientsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.clients_group_layout = QVBoxLayout()
        self.setLayout(self.clients_group_layout)
        # --------------------------- #

        # ----- Creating Clients Group ----- #
        self.clients_group = QGroupBox("Clients")
        self.clients_tab_layout = QVBoxLayout()
        self.clients_group.setLayout(self.clients_tab_layout)
        # ---------------------------------- #

        self.clients_group_layout.addWidget(self.clients_group)

        self.client_frames = {}  # key: client.process_id (dict), value: QFrame

        QTimer.singleShot(0, lambda: asyncio.create_task(self.update_hooked_client_info()))

    async def update_hooked_client_info(self):
        while True:
            # Remove clients that are no longer hooked
            for client_process_id in list(self.client_frames.keys()):
                if all(client_process_id != client.process_id for client in self.hooked_clients): # unreadable, i know
                    client_frame_info = self.client_frames.pop(client_process_id)
                    client_frame = client_frame_info['frame']
                    self.clients_tab_layout.removeWidget(client_frame)
                    client_frame.deleteLater()

            # Add new hooked clients
            for client in self.hooked_clients:
                if client.process_id not in self.client_frames:
                    client_frame = QGroupBox(client.title)
                    client_frame_layout = QVBoxLayout()

                    level_label = QLabel(f"Level: {await client.stats.reference_level()}")
                    health_label = QLabel(f"Health: {await client.stats.current_hitpoints()}/{await client.stats.max_hitpoints()}")
                    mana_label = QLabel(f"Mana: {await client.stats.current_mana()}/{await client.stats.max_mana()}")
                    energy_label = QLabel(f"Energy: {await client.current_energy()}/{await client.stats.energy_max() + await client.stats.bonus_energy()}")
                    position_label = QLabel(f"Position: {await client.body.position()}")
                    yaw_label = QLabel(f"Yaw: {await client.body.yaw()}")
                
                    client_frame_layout.addWidget(level_label)
                    client_frame_layout.addWidget(health_label)
                    client_frame_layout.addWidget(mana_label)
                    client_frame_layout.addWidget(energy_label)
                    client_frame_layout.addWidget(position_label)
                    client_frame_layout.addWidget(yaw_label)

                    self.client_frames[client.process_id] = {
                        'frame': client_frame,
                        'labels': {
                            'level': level_label,
                            'health': health_label,
                            'mana': mana_label,
                            'energy': energy_label,
                            'position': position_label,
                            'yaw': yaw_label
                        }
                    }

                    client_frame.setLayout(client_frame_layout)

                    #self.client_frames[client.title] = client_frame # sets the key (title) to the frame
                    self.clients_tab_layout.addWidget(client_frame, alignment=Qt.AlignmentFlag.AlignTop)

                else:
                    client_labels = self.client_frames[client.process_id]['labels']
                    client_labels['level'].setText(f"Level: {await client.stats.reference_level()}")
                    client_labels['health'].setText(f"Health: {await client.stats.current_hitpoints()}/{await client.stats.max_hitpoints()}")
                    client_labels['mana'].setText(f"Mana: {await client.stats.current_mana()}/{await client.stats.max_mana()}")
                    client_labels['energy'].setText(f"Energy: {await client.current_energy()}/{await client.stats.energy_max() + await client.stats.bonus_energy()}")
                    client_labels['position'].setText(f"Position: {await client.body.position()}")
                    client_labels['yaw'].setText(f"Yaw: {await client.body.yaw()}")

            await asyncio.sleep(1)

class TeleportsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.teleports_group_layout = QVBoxLayout()
        self.setLayout(self.teleports_group_layout)
        # --------------------------- #

        # ----- Creating Teleports Group ----- #
        self.teleports_group = QGroupBox("Teleports")
        self.teleports_tab_layout = QVBoxLayout()

        #self.teleports_tab_layout.addStretch()

        self.teleports_group.setLayout(self.teleports_tab_layout)
        self.teleports_group_layout.addWidget(self.teleports_group)
        # ------------------------------------ #

        # ----- Hunhau Teleport Button ----- #
        hunhau_teleport_button = QPushButton("Hunhau Teleport")

        hunhau_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #hunhau_teleport_button.setMaximumHeight(50)
        #hunhau_teleport_button.setMinimumHeight(50)

        hunhau_teleport_button.clicked.connect(lambda: asyncio.create_task(self.hunhau_teleport()))

        self.teleports_tab_layout.addWidget(hunhau_teleport_button)
        # ---------------------------------- #

        # ----- Voice of Death Teleport Button ----- #
        voice_of_death_teleport_button = QPushButton("Voice of Death Teleport")

        voice_of_death_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #voice_of_death_teleport_button.setMaximumHeight(50)
        #voice_of_death_teleport_button.setMinimumHeight(50)

        voice_of_death_teleport_button.clicked.connect(lambda: asyncio.create_task(self.voice_of_death_teleport()))

        self.teleports_tab_layout.addWidget(voice_of_death_teleport_button)
        # ------------------------------------------ #

        # ----- Xibalba Elemental Teleport Button ----- #
        xibalba_elemental_teleport_button = QPushButton("Xibalba Elemental Teleport")

        xibalba_elemental_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #xibalba_elemental_teleport_button.setMaximumHeight(50)
        #xibalba_elemental_teleport_button.setMinimumHeight(50)

        xibalba_elemental_teleport_button.clicked.connect(lambda: asyncio.create_task(self.xibalba_elemental_teleport()))

        self.teleports_tab_layout.addWidget(xibalba_elemental_teleport_button)
        # --------------------------------------------- #

        # ----- Unjail Teleport Button ----- #
        unjail_teleport_button = QPushButton("Unjail")

        unjail_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #unjail_teleport_button.setMaximumHeight(50)
        #unjail_teleport_button.setMinimumHeight(50)

        unjail_teleport_button.clicked.connect(lambda: asyncio.create_task(self.unjail()))

        self.teleports_tab_layout.addWidget(unjail_teleport_button)
        # ---------------------------------- #

    async def hunhau_teleport(self):
        print("[TELEPORTS] Hanhau Teleport pressed.")

        await self.utils.handle_basic_teleport(0, 0, 1832.625)

    async def voice_of_death_teleport(self):
        print("[TELEPORTS] Voice of Death Teleport pressed.")

        await self.utils.handle_basic_teleport(-1079.9241943359375, -23360.068359375, 1602.2117919921875)

    async def xibalba_elemental_teleport(self):
        print("[TELEPORTS] Xibalba Elemental Teleport pressed.")

        await self.utils.handle_basic_teleport(-6196.8505859375, 22107.2109375, 1881.55224609375)

    async def unjail(self):
        print("[TELEPORTS] Unjail pressed.")

        await self.utils.handle_basic_teleport(-8961.6376953125, -9641.5048828125, 1.4779052734375)

class FishTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        self.fish_hooking_tasks = {} # client: task
        self.fish_hooks = {} # client: oldbytes

        self.catch_all_fish_task = None

        # ----- Creating Layout ----- #
        self.fish_tab_layout = QVBoxLayout()
        self.setLayout(self.fish_tab_layout)
        # --------------------------- #

        # ----- Creating Fish Hook Group ----- #
        self.fish_hook_group = QGroupBox("Fish Hooks")
        self.fish_hook_group_layout = QHBoxLayout()
        # ------------------------------------ #

        # ----- Creating Fish Spots Group ----- #
        self.fish_spots_group = QGroupBox("Fish Spots")
        self.fish_spots_group_layout = QHBoxLayout()
        # ------------------------------------- #

        # ----- Creating Catch Fish Group ----- #
        self.catch_fish_group = QGroupBox("Catch Fish")
        self.catch_fish_group_layout = QHBoxLayout()
        # ------------------------------------- #

        # ----- Creating Fish Collectors Group ----- #
        self.fish_collectors_group = QGroupBox("Fish Collectors")
        self.fish_collectors_group_layout = QHBoxLayout()
        # ------------------------------------------ #

        # ----- Activate Fish Hooks Button ----- #
        activate_fish_hooks_button = QPushButton("Activate Fish Hooks")

        activate_fish_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #activate_fish_hooks_button.setMaximumHeight(50)
        activate_fish_hooks_button.setMinimumHeight(50)

        activate_fish_hooks_button.clicked.connect(lambda: asyncio.create_task(self.activate_fish_hooks()))

        self.fish_hook_group_layout.addWidget(activate_fish_hooks_button)
        # -------------------------------------- #

        # ----- Deactivate Fish Hooks Button ----- #
        deactivate_fish_hooks_button = QPushButton("Deactivate Fish Hooks")

        deactivate_fish_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #deactivate_fish_hooks_button.setMaximumHeight(50)
        deactivate_fish_hooks_button.setMinimumHeight(50)

        deactivate_fish_hooks_button.clicked.connect(lambda: asyncio.create_task(self.deactivate_fish_hooks()))

        self.fish_hook_group_layout.addWidget(deactivate_fish_hooks_button)
        # ---------------------------------------- #

        # ----- Fire Fish Spot Button ----- #
        fire_fish_spot_button = QPushButton("Fire Spot")

        fire_fish_spot_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #fire_fish_spot_button.setMaximumHeight(50)
        fire_fish_spot_button.setMinimumHeight(50)

        fire_fish_spot_button.clicked.connect(lambda: asyncio.create_task(self.fire_fish_spot()))

        self.fish_spots_group_layout.addWidget(fire_fish_spot_button)
        # --------------------------------- #

        # ----- Ice Fish Spot Button ----- #
        ice_fish_spot_button = QPushButton("Ice Spot")

        ice_fish_spot_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #ice_fish_spot_button.setMaximumHeight(50)
        ice_fish_spot_button.setMinimumHeight(50)

        ice_fish_spot_button.clicked.connect(lambda: asyncio.create_task(self.ice_fish_spot()))

        self.fish_spots_group_layout.addWidget(ice_fish_spot_button)
        # --------------------------------- #

        # ----- Myth Fish Spot Button ----- #
        myth_fish_spot_button = QPushButton("Myth Spot")

        myth_fish_spot_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #myth_fish_spot_button.setMaximumHeight(50)
        myth_fish_spot_button.setMinimumHeight(50)

        myth_fish_spot_button.clicked.connect(lambda: asyncio.create_task(self.myth_fish_spot()))

        self.fish_spots_group_layout.addWidget(myth_fish_spot_button)
        # --------------------------------- #

        # ----- Death Fish Spot Button ----- #
        death_fish_spot_button = QPushButton("Death Spot")

        death_fish_spot_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #death_fish_spot_button.setMaximumHeight(50)
        death_fish_spot_button.setMinimumHeight(50)

        death_fish_spot_button.clicked.connect(lambda: asyncio.create_task(self.death_fish_spot()))

        self.fish_spots_group_layout.addWidget(death_fish_spot_button)
        # ---------------------------------- #

        # ----- Catch Storm Fish Button ----- #
        storm_fish_button = QPushButton("Storm")

        storm_fish_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #storm_fish_button.setMaximumHeight(50)
        storm_fish_button.setMinimumHeight(50)

        storm_fish_button.clicked.connect(lambda: asyncio.create_task(self.catch_storm_fish()))

        self.catch_fish_group_layout.addWidget(storm_fish_button)
        # ---------------------------------- #

        # ----- Catch Fire Fish Button ----- #
        fire_fish_button = QPushButton("Fire")

        fire_fish_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #fire_fish_button.setMaximumHeight(50)
        fire_fish_button.setMinimumHeight(50)

        fire_fish_button.clicked.connect(lambda: asyncio.create_task(self.catch_fire_fish()))

        self.catch_fish_group_layout.addWidget(fire_fish_button)
        # --------------------------------- #

        # ----- Catch Ice Fish Button ----- #
        ice_fish_button = QPushButton("Ice")

        ice_fish_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #ice_fish_button.setMaximumHeight(50)
        ice_fish_button.setMinimumHeight(50)

        ice_fish_button.clicked.connect(lambda: asyncio.create_task(self.catch_ice_fish()))

        self.catch_fish_group_layout.addWidget(ice_fish_button)
        # -------------------------------- #

        # ----- Catch Myth Fish Button ----- #
        myth_fish_button = QPushButton("Myth")

        myth_fish_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #myth_fish_button.setMaximumHeight(50)
        myth_fish_button.setMinimumHeight(50)

        myth_fish_button.clicked.connect(lambda: asyncio.create_task(self.catch_myth_fish()))

        self.catch_fish_group_layout.addWidget(myth_fish_button)
        # --------------------------------- #

        # ----- Catch Death Fish Button ----- #
        death_fish_button = QPushButton("Death")

        death_fish_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #death_fish_button.setMaximumHeight(50)
        death_fish_button.setMinimumHeight(50)

        death_fish_button.clicked.connect(lambda: asyncio.create_task(self.catch_death_fish()))

        self.catch_fish_group_layout.addWidget(death_fish_button)
        # ---------------------------------- #

        # ----- Catch All Fish Button ----- #
        all_fish_button = QPushButton("All")

        all_fish_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #all_fish_button.setMaximumHeight(50)
        all_fish_button.setMinimumHeight(50)

        all_fish_button.clicked.connect(lambda: asyncio.create_task(self.catch_all_fish()))

        self.catch_fish_group_layout.addWidget(all_fish_button)
        # ---------------------------------- #

        # ----- East Fish Collector Button ----- #
        east_fish_collector_button = QPushButton("East")

        east_fish_collector_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #east_fish_collector_button.setMaximumHeight(50)
        east_fish_collector_button.setMinimumHeight(50)

        east_fish_collector_button.clicked.connect(lambda: asyncio.create_task(self.east_fish_collector_teleport()))

        self.fish_collectors_group_layout.addWidget(east_fish_collector_button)
        # -------------------------------------- #

        # ----- North Fish Collector Button ----- #
        north_fish_collector_button = QPushButton("North")

        north_fish_collector_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #north_fish_collector_button.setMaximumHeight(50)
        north_fish_collector_button.setMinimumHeight(50)

        north_fish_collector_button.clicked.connect(lambda: asyncio.create_task(self.north_fish_collector_teleport()))

        self.fish_collectors_group_layout.addWidget(north_fish_collector_button)
        # -------------------------------------- #

        # ----- Far West Fish Collector Button ----- #
        far_west_fish_collector_button = QPushButton("Far West")

        far_west_fish_collector_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #far_west_fish_collector_button.setMaximumHeight(50)
        far_west_fish_collector_button.setMinimumHeight(50)

        far_west_fish_collector_button.clicked.connect(lambda: asyncio.create_task(self.far_west_fish_collector_teleport()))

        self.fish_collectors_group_layout.addWidget(far_west_fish_collector_button)
        # ------------------------------------------ #

        # ----- Close West Fish Collector Button ----- #
        close_west_fish_collector_button = QPushButton("Close West")

        close_west_fish_collector_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #close_west_fish_collector_button.setMaximumHeight(50)
        close_west_fish_collector_button.setMinimumHeight(50)

        close_west_fish_collector_button.clicked.connect(lambda: asyncio.create_task(self.close_west_fish_collector_teleport()))

        self.fish_collectors_group_layout.addWidget(close_west_fish_collector_button)
        # -------------------------------------------- #

        # ----- South Fish Collector Button ----- #
        south_fish_collector_button = QPushButton("South")

        south_fish_collector_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #south_fish_collector_button.setMaximumHeight(50)
        south_fish_collector_button.setMinimumHeight(50)

        south_fish_collector_button.clicked.connect(lambda: asyncio.create_task(self.south_fish_collector_teleport()))

        self.fish_collectors_group_layout.addWidget(south_fish_collector_button)
        # --------------------------------------- #

        self.fish_hook_group.setLayout(self.fish_hook_group_layout)
        self.fish_spots_group.setLayout(self.fish_spots_group_layout)
        self.catch_fish_group.setLayout(self.catch_fish_group_layout)
        self.fish_collectors_group.setLayout(self.fish_collectors_group_layout)

        self.fish_tab_layout.addWidget(self.fish_hook_group)
        self.fish_tab_layout.addWidget(self.fish_spots_group)
        self.fish_tab_layout.addWidget(self.catch_fish_group)
        self.fish_tab_layout.addWidget(self.fish_collectors_group)

    async def activate_fish_hooks(self):
        print(f"[FISH] Activate Fish Hooks pressed.")
        client = self.utils.foreground_client # I was **not** to use this in main, but cannot think of any other way.

        if client not in self.fish_hooks:
            self.fish_hooking_tasks[client] = asyncio.create_task(self.utils.patch_fish(client))

            addr_oldbytes = await self.fish_hooking_tasks[client]
            self.fish_hooks[client] = addr_oldbytes

            self.fish_hooking_tasks.pop(client, None)
                
    async def deactivate_fish_hooks(self):
        print(f"[FISH] Deactivate Fish Hooks pressed.")
        client = self.utils.foreground_client

        if client in self.fish_hooks:
            asyncio.create_task(self.utils.reset_fish_patch(client, self.fish_hooks[client]))
            self.fish_hooks.pop(client, None)
            return

        print(f"[FISH] Fish Hooks are not active.")

    async def fire_fish_spot(self):
        print(f"[FISH] Fire Spot pressed.")

        await self.utils.handle_basic_teleport(13839.333984375, 16147.3603515625, -383.54107666015625)

    async def ice_fish_spot(self):
        print(f"[FISH] Ice Spot pressed.")

        await self.utils.handle_basic_teleport(12079.072265625, 7716.85009765625, -24.98236083984375)

    async def myth_fish_spot(self):
        print(f"[FISH] Myth Spot pressed.")

        await self.utils.handle_basic_teleport(-23877.533203125, 1532.796875, -37.36785888671875)

    async def death_fish_spot(self):
        print(f"[FISH] Death Spot pressed.")

        await self.utils.handle_basic_teleport(-21278.697265625, -5701.77587890625, 321.2095642089844)

    async def catch_storm_fish(self):
        print(f"[FISH] Catch Storm Fish pressed.")

        if not self.fish_hooks:
            print(f"[FISH] Fish hooks are not active.")
            return

        await self.utils.catch_fish("Storm")

    async def catch_fire_fish(self):
        print(f"[FISH] Catch Fire Fish pressed.")

        if not self.fish_hooks:
            print(f"[FISH] Fish hooks are not active.")
            return

        await self.utils.catch_fish("Fire")

    async def catch_ice_fish(self):
        print(f"[FISH] Catch Ice Fish pressed.")

        if not self.fish_hooks:
            print(f"[FISH] Fish hooks are not active.")
            return

        await self.utils.catch_fish("Ice")

    async def catch_myth_fish(self):
        print(f"[FISH] Catch Myth Fish pressed.")

        if not self.fish_hooks:
            print(f"[FISH] Fish hooks are not active.")
            return

        await self.utils.catch_fish("Myth")

    async def catch_death_fish(self):
        print(f"[FISH] Catch Death Fish pressed.")

        if not self.fish_hooks:
            print(f"[FISH] Fish hooks are not active.")
            return
        
        await self.utils.catch_fish("Death")

    async def catch_all_fish(self):
        print(f"[FISH] Catch All Fish pressed.")

        if not self.fish_hooks:
            print(f"[FISH] Fish hooks are not active.")
            return

        if not self.catch_all_fish_task:
            self.catch_all_fish_task = asyncio.create_task(self.utils.catch_all_fish())
            return
        
        if self.catch_all_fish_task:
            self.catch_all_fish_task.cancel()
            self.catch_all_fish_task = None
            print("[FISH] Cancelled catching all fish.")

    async def east_fish_collector_teleport(self):
        print(f"[FISH] East Fish Collector teleport pressed.")

        await self.utils.handle_basic_teleport(9051.5634765625, 2402.267578125, 6.117401123046875)

    async def north_fish_collector_teleport(self):
        print(f"[FISH] North Fish Collector teleport pressed.")

        await self.utils.handle_basic_teleport(2399.4384765625, 8997.7275390625, 3.51953125)

    async def far_west_fish_collector_teleport(self):
        print(f"[FISH] Far West Fish Collector teleport pressed.")

        await self.utils.handle_basic_teleport(-9563.4072265625, 719.537841796875, 2.247711181640625)

    async def close_west_fish_collector_teleport(self):
        print(f"[FISH] Close West Fish Collector teleport pressed.")

        await self.utils.handle_basic_teleport(-5133.890625, 1290.77685546875, 429.2041015625)

    async def south_fish_collector_teleport(self):
        print(f"[FISH] South Fish Collector teleport pressed.")

        await self.utils.handle_basic_teleport(-788.6144409179688, -8821.65625, 33.06304931640625)

class TouchstonesTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.touchstones_group_layout = QVBoxLayout()
        self.setLayout(self.touchstones_group_layout)
        # --------------------------- #

        # ----- Creating Touchstones Group ----- #
        self.touchstones_group = QGroupBox("Touchstones")

        self.touchstones_tab_layout = QVBoxLayout()

        self.touchstones_column_layout = QHBoxLayout()

        self.left_touchstones_column = QVBoxLayout()
        self.touchstones_column_layout.addLayout(self.left_touchstones_column)

        self.right_touchstones_column = QVBoxLayout()
        self.touchstones_column_layout.addLayout(self.right_touchstones_column)

        self.touchstones_tab_layout.addLayout(self.touchstones_column_layout)

        self.touchstones_group.setLayout(self.touchstones_tab_layout)
        self.touchstones_group_layout.addWidget(self.touchstones_group)
        # -------------------------------------- #

        # ----- Ice Touchstone Button ----- #
        ice_touchstone_button = QPushButton("Ice Touchstone")

        ice_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #ice_touchstone_button.setMaximumHeight(50)
        #ice_touchstone_button.setMinimumHeight(50)

        ice_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.ice_touchstone_freecam_teleport()))

        self.left_touchstones_column.addWidget(ice_touchstone_button)
        # ---------------------------------- #

        # ----- Storm Touchstone Button ----- #
        storm_touchstone_button = QPushButton("Storm Touchstone")

        storm_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #storm_touchstone_button.setMaximumHeight(50)
        #storm_touchstone_button.setMinimumHeight(50)

        storm_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.storm_touchstone_freecam_teleport()))

        self.left_touchstones_column.addWidget(storm_touchstone_button)
        # ----------------------------------- #

        # ----- Fire Touchstone Button ----- #
        fire_touchstone_button = QPushButton("Fire Touchstone")

        fire_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #fire_touchstone_button.setMaximumHeight(50)
        #fire_touchstone_button.setMinimumHeight(50)

        fire_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.fire_touchstone_freecam_teleport()))

        self.left_touchstones_column.addWidget(fire_touchstone_button)
        # --------------------------------- #

        # ----- Life Touchstone Button ----- #
        life_touchstone_button = QPushButton("Life Touchstone")

        life_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #life_touchstone_button.setMaximumHeight(50)
        #life_touchstone_button.setMinimumHeight(50)

        life_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.life_touchstone_freecam_teleport()))

        self.right_touchstones_column.addWidget(life_touchstone_button)
        # --------------------------------- #

        # ----- Myth Touchstone Button ----- #
        myth_touchstone_button = QPushButton("Myth Touchstone")

        myth_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #myth_touchstone_button.setMaximumHeight(50)
        #myth_touchstone_button.setMinimumHeight(50)

        myth_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.myth_touchstone_freecam_teleport()))

        self.right_touchstones_column.addWidget(myth_touchstone_button)
        # --------------------------------- #

        # ----- Death Touchstone Button ----- #
        death_touchstone_button = QPushButton("Death Touchstone")

        death_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #death_touchstone_button.setMaximumHeight(50)
        #death_touchstone_button.setMinimumHeight(50)

        death_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.death_touchstone_freecam_teleport()))

        self.right_touchstones_column.addWidget(death_touchstone_button)
        # ---------------------------------- #

        # ----- Balance Touchstone Button ----- #
        balance_touchstone_button = QPushButton("Balance Touchstone")

        balance_touchstone_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        balance_touchstone_button.setMaximumHeight(90)
        balance_touchstone_button.setMinimumHeight(90)

        balance_touchstone_button.clicked.connect(lambda: asyncio.create_task(self.balance_touchstone_freecam_teleport()))

        self.touchstones_tab_layout.addWidget(balance_touchstone_button)
        # ------------------------------------ #

    async def ice_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Ice Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Ice_01")

    async def storm_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Storm Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Storm_01")

    async def fire_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Fire Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Fire_01")

    async def life_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Life Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Life_01")

    async def myth_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Myth Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Myth_01")

    async def death_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Death Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Death_01")

    async def balance_touchstone_freecam_teleport(self):
        print(f"[TOUCHSTONES] Balance Touchstone pressed.")

        await self.utils.entity_freecam_teleport("Raid_CantripObject_Balance_01")

class DrumsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients
        
        self.auto_drums_task = None

        # ----- Creating Layout ----- #
        self.drums_group_layout = QVBoxLayout()
        self.setLayout(self.drums_group_layout)
        # --------------------------- #

        # ----- Creating Drums Group ----- #
        self.drums_group = QGroupBox("Teleports")
        self.drums_tab_layout = QHBoxLayout()

        #self.drums_tab_layout.addStretch()

        self.drums_group.setLayout(self.drums_tab_layout)
        self.drums_group_layout.addWidget(self.drums_group)
        # --------------------------------- #

        # ----- Drum Teleport Button ----- #
        drum_teleport_button = QPushButton("Drum Teleport")

        drum_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #drum_teleport_button.setMaximumHeight(50)
        #drum_teleport_button.setMinimumHeight(50)

        drum_teleport_button.clicked.connect(lambda: asyncio.create_task(self.drum_teleport()))

        self.drums_tab_layout.addWidget(drum_teleport_button)
        # -------------------------------- #

        # ----- Auto Drums Button ----- #
        auto_drums_button = QPushButton("Auto Drums")

        auto_drums_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #auto_drums_button.setMaximumHeight(50)
        #auto_drums_button.setMinimumHeight(50)

        auto_drums_button.clicked.connect(lambda: asyncio.create_task(self.auto_drums()))

        self.drums_tab_layout.addWidget(auto_drums_button)
        # ---------------------------- #

    async def drum_teleport(self):
        print("[DRUMS] Drum Teleport pressed.")

        await self.utils.raid_drum_teleport()

    async def auto_drums(self):
        print("[DRUMS] Auto Drums pressed.")
        
        if not self.auto_drums_task:
            self.auto_drums_task = asyncio.create_task(self.utils.auto_raid_drums())
            return
        
        if self.auto_drums_task:
            self.auto_drums_task.cancel()
            self.auto_drums_task = None

class TokensTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.tokens_tab_layout = QVBoxLayout()
        self.setLayout(self.tokens_tab_layout)
        # --------------------------- #

        # ----- Creating Chest Group ----- #
        self.tokens_group = QGroupBox("Tokens")
        self.tokens_group_layout = QVBoxLayout()
        # -------------------------------- #

        # ----- Read Tokens Button ----- #
        read_tokens_button = QPushButton("Read Tokens")

        read_tokens_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #read_tokens_button.setMaximumHeight(50)
        read_tokens_button.setMinimumHeight(50)

        read_tokens_button.clicked.connect(lambda: asyncio.create_task(self.handle_token_reading()))

        self.tokens_group_layout.addWidget(read_tokens_button)
        # ------------------------------------ #

        # ----- Wildlife Coin Teleport Button ----- #
        wildlife_coin_teleport_button = QPushButton("Wildlife Coin Teleport")

        wildlife_coin_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #wildlife_coin_teleport_button.setMaximumHeight(50)
        wildlife_coin_teleport_button.setMinimumHeight(50)

        wildlife_coin_teleport_button.clicked.connect(lambda: asyncio.create_task(self.handle_wildlife_coin_teleport()))

        self.tokens_group_layout.addWidget(wildlife_coin_teleport_button)
        # ------------------------------------ #

        # ----- Elements Coin Teleport Button ----- #
        elements_coin_teleport_button = QPushButton("Elements Coin Teleport")

        elements_coin_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #elements_coin_teleport_button.setMaximumHeight(50)
        elements_coin_teleport_button.setMinimumHeight(50)

        elements_coin_teleport_button.clicked.connect(lambda: asyncio.create_task(self.handle_elements_coin_teleport()))

        self.tokens_group_layout.addWidget(elements_coin_teleport_button)
        # ------------------------------------ #

        # ----- Cosmic Coin Teleport Button ----- #
        cosmic_coin_teleport_button = QPushButton("Cosmic Coin Teleport")

        cosmic_coin_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #cosmic_coin_teleport_button.setMaximumHeight(50)
        cosmic_coin_teleport_button.setMinimumHeight(50)

        cosmic_coin_teleport_button.clicked.connect(lambda: asyncio.create_task(self.handle_cosmic_coin_teleport()))

        self.tokens_group_layout.addWidget(cosmic_coin_teleport_button)
        # ------------------------------------ #

        self.tokens_group.setLayout(self.tokens_group_layout)
        self.tokens_tab_layout.addWidget(self.tokens_group)

    async def handle_token_reading(self):
        print("[TOKENS] Read Tokens pressed.")

        if tokens := await self.utils.read_tokens():
            print(tokens)

    async def handle_wildlife_coin_teleport(self):
        print("[TOKENS] Wildlife Coin Teleport pressed.")

        await self.utils.token_teleport("RAID-Coins-Wildlife-INVISO_01")

    async def handle_elements_coin_teleport(self):
        print("[TOKENS] Elements Coin Teleport pressed.")

        await self.utils.token_teleport("RAID-Coins-Elements-INVISO_01")

    async def handle_cosmic_coin_teleport(self):
        print("[TOKENS] Cosmic Coin Teleport pressed.")

        await self.utils.token_teleport("RAID-Coins-Cosmic-INVISO_01")

class MiscTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.misc_tab_layout = QVBoxLayout()
        self.setLayout(self.misc_tab_layout)
        # --------------------------- #

        # ----- Creating Chest Group ----- #
        self.cacao_pods_group = QGroupBox("Cacao Pods")
        self.cacao_pods_group_layout = QVBoxLayout()
        # -------------------------------- #

        # ----- Creating Misfortune Tears Group ----- #
        self.misfortune_tears_group = QGroupBox("Misfortune Tears")
        self.misfortune_tears_group_layout = QVBoxLayout()
        # ------------------------------------------- #

        # ----- Cacao Pod Teleport Button ----- #
        cacao_pod_teleport_button = QPushButton("Cacao Pod Teleport")

        cacao_pod_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        cacao_pod_teleport_button.setMaximumHeight(50)
        cacao_pod_teleport_button.setMinimumHeight(50)

        cacao_pod_teleport_button.clicked.connect(lambda: asyncio.create_task(self.cacao_pod_teleport()))

        self.cacao_pods_group_layout.addWidget(cacao_pod_teleport_button)
        # ------------------------------------ #

        # ----- Grab Cacao Pod Button ----- #
        grab_cacao_pod_button = QPushButton("Grab Cacao Pod")

        grab_cacao_pod_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        grab_cacao_pod_button.setMaximumHeight(50)
        grab_cacao_pod_button.setMinimumHeight(50)

        grab_cacao_pod_button.clicked.connect(lambda: asyncio.create_task(self.grab_cacao_pod()))

        self.cacao_pods_group_layout.addWidget(grab_cacao_pod_button)
        # --------------------------------- #

        # ----- Cacao Pod Collector Teleport Button ----- #
        cacao_pod_collector_teleport_button = QPushButton("Cacao Pod Collector Teleport")

        cacao_pod_collector_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        cacao_pod_collector_teleport_button.setMaximumHeight(50)
        cacao_pod_collector_teleport_button.setMinimumHeight(50)

        cacao_pod_collector_teleport_button.clicked.connect(lambda: asyncio.create_task(self.cacao_pod_collector_teleport()))

        self.cacao_pods_group_layout.addWidget(cacao_pod_collector_teleport_button)
        # ----------------------------------------------- #

        # ----- Misfortune Tear Teleport Button ----- #
        misfortune_tear_teleport_button = QPushButton("Misfortune Tear Teleport")

        misfortune_tear_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        misfortune_tear_teleport_button.setMaximumHeight(50)
        misfortune_tear_teleport_button.setMinimumHeight(50)

        misfortune_tear_teleport_button.clicked.connect(lambda: asyncio.create_task(self.misfortune_tear_teleport()))

        self.misfortune_tears_group_layout.addWidget(misfortune_tear_teleport_button)
        # ------------------------------------------ #

        # ----- Grab Misfortune Tear Button ----- #
        grab_misfortune_tear_button = QPushButton("Grab Misfortune Tear")

        grab_misfortune_tear_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        grab_misfortune_tear_button.setMaximumHeight(50)
        grab_misfortune_tear_button.setMinimumHeight(50)

        grab_misfortune_tear_button.clicked.connect(lambda: asyncio.create_task(self.grab_misfortune_tear()))

        self.misfortune_tears_group_layout.addWidget(grab_misfortune_tear_button)
        # --------------------------------------- #

        # ----- Misfortune Tear Collector Teleport Button ----- #
        misfortune_tear_collector_teleport_button = QPushButton("Misfortune Tear Collector Teleport")

        misfortune_tear_collector_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        misfortune_tear_collector_teleport_button.setMaximumHeight(50)
        misfortune_tear_collector_teleport_button.setMinimumHeight(50)

        misfortune_tear_collector_teleport_button.clicked.connect(lambda: asyncio.create_task(self.misfortune_tear_collector_teleport()))

        self.misfortune_tears_group_layout.addWidget(misfortune_tear_collector_teleport_button)
        # ------------------------------------------------------ #

        self.cacao_pods_group.setLayout(self.cacao_pods_group_layout)
        self.misfortune_tears_group.setLayout(self.misfortune_tears_group_layout)

        self.misc_tab_layout.addWidget(self.cacao_pods_group)
        self.misc_tab_layout.addWidget(self.misfortune_tears_group)

    async def cacao_pod_teleport(self):
        print(f"[MISC.] Cacao Pod Teleport pressed.")

        await self.utils.entity_teleport("Raid_AZ_Cacao")

    async def grab_cacao_pod(self):
        print(f"[MISC.] Grab Cacao Pod pressed.")

        await self.utils.grab_item("Raid_AZ_Cacao")

    async def cacao_pod_collector_teleport(self):
        print(f"[MISC.] Cacao Pod Collector Teleport pressed.")

        await self.utils.handle_basic_teleport(-5003.6220703125, -1322.1357421875, 429.2038269042969)

    async def misfortune_tear_teleport(self):
        print(f"[MISC.] Misfortune Tear Teleport pressed.")

        await self.utils.entity_teleport("Raid_Jewel_Reagent")

    async def grab_misfortune_tear(self):
        print(f"[MISC.] Grab Misfortune Tear pressed.")

        await self.utils.grab_item("Raid_Jewel_Reagent")

    async def misfortune_tear_collector_teleport(self):
        print(f"[MISC.] Cacao Pod Collector Teleport pressed.")

        await self.utils.handle_basic_teleport(-17500.33984375, -3915.417236328125, 1.649688720703125)

class UtilityTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        self.auto_dialogue_tasks = {}
        self.speedhack_tasks = {}
        self.freecam_task = None

        # ----- Creating Layout ----- #
        self.utility_group_layout = QVBoxLayout()
        self.setLayout(self.utility_group_layout)
        # --------------------------- #

        # ----- Creating Utility Group ----- #
        self.utility_group = QGroupBox("Utility")
        self.utility_tab_layout = QVBoxLayout()

        #self.utility_tab_layout.addStretch()

        self.utility_group.setLayout(self.utility_tab_layout)
        self.utility_group_layout.addWidget(self.utility_group)
        # ---------------------------------- #

        # ----- Auto Dialogue Button ----- #
        auto_dialogue_button = QPushButton("Toggle Auto Dialogue")

        auto_dialogue_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #auto_dialogue_button.setMaximumHeight(50)
        #auto_dialogue_button.setMinimumHeight(50)

        auto_dialogue_button.clicked.connect(lambda: asyncio.create_task(self.toggle_auto_dialogue()))

        self.utility_tab_layout.addWidget(auto_dialogue_button)
        # -------------------------------- #

        # ----- Speedhack Button ----- #
        speedhack_button = QPushButton("Toggle Speedhack")

        speedhack_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #speedhack_button.setMaximumHeight(50)
        #speedhack_button.setMinimumHeight(50)

        speedhack_button.clicked.connect(lambda: asyncio.create_task(self.toggle_speedhack()))

        self.utility_tab_layout.addWidget(speedhack_button)
        # ---------------------------- #

        # ----- Freecam Button ----- #
        freecam_button = QPushButton("Toggle Freecam")

        freecam_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #freecam_button.setMaximumHeight(50)
        #freecam_button.setMinimumHeight(50)

        freecam_button.clicked.connect(lambda: asyncio.create_task(self.toggle_freecam()))

        self.utility_tab_layout.addWidget(freecam_button)
        # -------------------------- #

        # ----- Freecam Teleport Button ----- #
        freecam_teleport_button = QPushButton("Freecam Teleport")

        freecam_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #freecam_teleport_button.setMaximumHeight(50)
        #freecam_teleport_button.setMinimumHeight(50)

        freecam_teleport_button.clicked.connect(lambda: asyncio.create_task(self.handle_freecam_teleport()))

        self.utility_tab_layout.addWidget(freecam_teleport_button)
        # ---------------------------------- #

        # ----- XYZ Sync Button ----- #
        xyz_sync_button = QPushButton("XYZ Sync")

        xyz_sync_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #xyz_sync_button.setMaximumHeight(50)
        #xyz_sync_button.setMinimumHeight(50)

        xyz_sync_button.clicked.connect(lambda: asyncio.create_task(self.handle_xyz_sync()))

        self.utility_tab_layout.addWidget(xyz_sync_button)
        # --------------------------- #

        # ----- Copy Position Button ----- #
        copy_position_button = QPushButton("Copy Position")

        copy_position_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #copy_position_button.setMaximumHeight(50)
        #copy_position_button.setMinimumHeight(50)

        copy_position_button.clicked.connect(lambda: asyncio.create_task(self.handle_copy_position()))

        self.utility_tab_layout.addWidget(copy_position_button)
        # -------------------------------- #

    async def toggle_auto_dialogue(self):
        print("[UTILITY] Auto Dialogue pressed.")
        
        if not self.auto_dialogue_tasks:
            for client in self.hooked_clients:
                self.auto_dialogue_tasks[client] = asyncio.create_task(self.utils.handle_auto_dialogue(client))
            return
        
        if self.auto_dialogue_tasks:
            for client, auto_dialogue_task in self.auto_dialogue_tasks.items():
                auto_dialogue_task.cancel()
            self.auto_dialogue_tasks = {}

    async def toggle_speedhack(self):
        print("[UTILITY] Speedhack pressed.")
        
        if not self.speedhack_tasks:
            for client in self.hooked_clients:
                self.speedhack_tasks[client] = asyncio.create_task(self.utils.handle_speedhack(client))
            return
        
        if self.speedhack_tasks:
            for client, speedhack_task in self.speedhack_tasks.items():
                speedhack_task.cancel()
            self.speedhack_tasks = {}

    async def toggle_freecam(self):
        print("[UTILITY] Freecam pressed.")

        if not self.freecam_task:
            if self.hooked_clients:
                self.freecam_task = asyncio.create_task(self.utils.handle_freecam())
                return
        
        if self.freecam_task:
            self.freecam_task.cancel()
            self.freecam_task = None
            print(f"[TOGGLE] Freecam cancelled.") # i dont like this here but i was forced to

    async def handle_freecam_teleport(self):
        print("[UTILITY] Freecam Teleport pressed.")

        if not self.freecam_task:
            print(f"[UTILITY] Freecam is not active.")

        if self.freecam_task:
            self.freecam_task.cancel()
        
            camera_pos = await self.freecam_task

            self.freecam_task = None

            self.freecam_teleport_task = asyncio.create_task(self.utils.freecam_teleport(camera_pos))

    async def handle_xyz_sync(self):
        print("[UTILITY] XYZ Sync pressed.")

        await self.utils.xyz_sync()

    async def handle_copy_position(self):
        print("[UTILITY] Copy Position pressed.")

        await self.utils.copy_position()

class ThemesTab(QWidget):
    def __init__(self, themes: Themes):
        super().__init__()
        self.themes = themes

        # ----- Creating Layout ----- #
        self.themes_tab_layout = QVBoxLayout()
        self.setLayout(self.themes_tab_layout)
        # --------------------------- #

        # ----- Creating Main Themes Group ----- #
        self.main_themes_group = QGroupBox("Main Themes")
        self.main_themes_group_layout = QVBoxLayout()
        # -------------------------------------- #

        # ----- Creating Preset Themes Group ----- #
        self.preset_themes_group = QGroupBox("Preset Themes")
        self.preset_themes_group_layout = QVBoxLayout()
        # ---------------------------------------- #

        # ----- Default Theme Button ----- #
        default_theme_button_button = QPushButton("Default Theme")

        default_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #default_theme_button_button.setMaximumHeight(50)
        #default_theme_button_button.setMinimumHeight(50)

        default_theme_button_button.clicked.connect(self.enable_default_theme)

        self.main_themes_group_layout.addWidget(default_theme_button_button)
        # -------------------------------- #

        # ----- Azteca Theme Button ----- #
        azteca_theme_button_button = QPushButton("Azteca Theme")

        azteca_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #azteca_theme_button_button.setMaximumHeight(50)
        #azteca_theme_button_button.setMinimumHeight(50)

        azteca_theme_button_button.clicked.connect(self.enable_azteca_theme)

        self.main_themes_group_layout.addWidget(azteca_theme_button_button)
        # ------------------------------- #

        # ----- Custom Theme Button ----- #
        custom_theme_button_button = QPushButton("Custom Theme")

        custom_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #custom_theme_button_button.setMaximumHeight(50)
        #custom_theme_button_button.setMinimumHeight(50)

        custom_theme_button_button.clicked.connect(self.enable_custom_theme)

        self.main_themes_group_layout.addWidget(custom_theme_button_button)
        # ------------------------------- #

        # ----- Night Theme Button ----- #
        night_theme_button_button = QPushButton("Night Theme")

        night_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #night_theme_button_button.setMaximumHeight(50)
        #night_theme_button_button.setMinimumHeight(50)

        night_theme_button_button.clicked.connect(self.enable_night_theme)

        self.preset_themes_group_layout.addWidget(night_theme_button_button)
        # ------------------------------ #

        # ----- Celestia Theme Button ----- #
        celestia_theme_button_button = QPushButton("Celestia Theme")

        celestia_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #celestia_theme_button_button.setMaximumHeight(50)
        #celestia_theme_button_button.setMinimumHeight(50)

        celestia_theme_button_button.clicked.connect(self.enable_celestia_theme)

        self.preset_themes_group_layout.addWidget(celestia_theme_button_button)
        # --------------------------------- #
        
        # ----- Mooshu Theme Button ----- #
        mooshu_theme_button_button = QPushButton("Mooshu Theme")

        mooshu_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #mooshu_theme_button_button.setMaximumHeight(50)
        #mooshu_theme_button_button.setMinimumHeight(50)

        mooshu_theme_button_button.clicked.connect(self.enable_mooshu_theme)

        self.preset_themes_group_layout.addWidget(mooshu_theme_button_button)
        # ------------------------------- #

        self.main_themes_group.setLayout(self.main_themes_group_layout)
        self.preset_themes_group.setLayout(self.preset_themes_group_layout)

        self.themes_tab_layout.addWidget(self.main_themes_group)
        self.themes_tab_layout.addWidget(self.preset_themes_group)

    def enable_default_theme(self):
        print(f"[THEMES] Default theme enabled.")

        self.window().setStyleSheet(self.themes.default)

    def enable_azteca_theme(self):
        print(f"[THEMES] Azteca theme enabled.")

        self.window().setStyleSheet(self.themes.azteca)

    def enable_custom_theme(self):
        print(f"[THEMES] Custom theme enabled.")

        self.window().setStyleSheet(self.themes.custom_theme)

    def enable_night_theme(self):
        print(f"[THEMES] Night theme enabled.")

        self.window().setStyleSheet(self.themes.night)

    def enable_celestia_theme(self):
        print(f"[THEMES] Celestia theme enabled.")

        self.window().setStyleSheet(self.themes.celestia)

    def enable_mooshu_theme(self):
        print(f"[THEMES] Mooshu theme enabled.")

        self.window().setStyleSheet(self.themes.mooshu)

class MainWindow(QWidget):
    def __init__(self, loop: QEventLoop):
        super().__init__()
        self.loop = loop

        self.hooked_clients = []
        self.utils = Utils()
        self.themes = Themes()

        self.always_on_top_config = self.utils.read_config()["always_on_top"]
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.always_on_top_config)

        self.enable_clients_tab = self.utils.read_config()["enable_clients_tab"]

        self.use_raid_theme = self.utils.read_config()["use_raid_theme"]

        if self.use_raid_theme:
            self.window().setStyleSheet(self.themes.azteca)

        self.setWindowTitle("Crying Sky Cheat Tool - Lxghtend")
        self.resize(668, 400)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North) # Changes tab position, North: Top, South: Bottom, West: Left, East: Right

        self.hooks_tab = HooksTab(self.utils, self.hooked_clients)
        if self.enable_clients_tab:
            self.clients_tab = ClientsTab(self.utils, self.hooked_clients)
        self.teleports_tab = TeleportsTab(self.utils, self.hooked_clients)
        self.fish_tab = FishTab(self.utils, self.hooked_clients)
        self.touchstones_tab = TouchstonesTab(self.utils, self.hooked_clients)
        self.drums_tab = DrumsTab(self.utils, self.hooked_clients)
        self.tokens_tab = TokensTab(self.utils, self.hooked_clients)
        self.misc_tab = MiscTab(self.utils, self.hooked_clients)
        self.utility_tab = UtilityTab(self.utils, self.hooked_clients)
        self.themes_tab = ThemesTab(self.themes)

        tabs.addTab(self.hooks_tab, "Hooks")
        if self.enable_clients_tab:
            tabs.addTab(self.clients_tab, "Clients")
        tabs.addTab(self.teleports_tab, "Teleports")
        tabs.addTab(self.fish_tab, "Fish")
        tabs.addTab(self.touchstones_tab, "Touchstones")
        tabs.addTab(self.drums_tab, "Drums")
        tabs.addTab(self.tokens_tab, "Tokens")
        tabs.addTab(self.misc_tab, "Misc.")
        tabs.addTab(self.utility_tab, "Utility")
        tabs.addTab(self.themes_tab, "Themes")

        layout.addWidget(tabs)

        # Creating footer

        footers_layout = QHBoxLayout()

        donation_link_label = QLabel('<a href="https://www.buymeacoffee.com/lxghtend">Donate</a>', alignment=Qt.AlignmentFlag.AlignLeft)
        credit_label = QLabel('Made by Lxghtend (<a href="https://github.com/Lxghtend">https://github.com/Lxghtend</a>)', alignment=Qt.AlignmentFlag.AlignRight)

        donation_link_label.setOpenExternalLinks(True)
        credit_label.setOpenExternalLinks(True)

        footers_layout.addWidget(donation_link_label)
        footers_layout.addWidget(credit_label)

        layout.addLayout(footers_layout)

        self.start_keybinds()
        
    def start_keybinds(self):
        def run_threadsafe(coroutine):
            asyncio.run_coroutine_threadsafe(coroutine, self.loop)

        keybinds = {
            self.utils.read_config()["handle_xyz_sync"]: self.utility_tab.handle_xyz_sync,
            self.utils.read_config()["toggle_auto_dialogue"]: self.utility_tab.toggle_auto_dialogue,
            self.utils.read_config()["toggle_speedhack"]: self.utility_tab.toggle_speedhack,
            self.utils.read_config()["toggle_freecam"]: self.utility_tab.toggle_freecam,
            self.utils.read_config()["handle_freecam_teleport"]: self.utility_tab.handle_freecam_teleport
        }

        for keybind, function in keybinds.items():
            keyboard.add_hotkey(keybind, lambda func=function: run_threadsafe(func()))

class DisclaimerDialog(QDialog):
    def __init__(self, parent: MainWindow = None):
        super().__init__(parent)

        self.setWindowTitle("Disclaimer")
        self.setFixedSize(210, 150)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        label = QLabel("Please consider donating to\nsupport future development.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        donate_button = QPushButton("Donate")
        donate_button.clicked.connect(self.open_donate)

        ok_button = QPushButton("Ok")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addWidget(donate_button)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def open_donate(self):
        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/lxghtend"))

def main():
    app = QApplication(sys.argv)

    appid = "lxghtend.cryingsky.tool.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    app.setWindowIcon(QIcon("icon.ico"))

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(loop)
    window.show()

    disclaimer = DisclaimerDialog(window)
    disclaimer.show()

    with loop:
        loop.run_forever()

    #sys.exit(app.exec())

if __name__ == "__main__":
    main()