import sys
import ctypes
import asyncio
import keyboard
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication, QLabel, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSizePolicy, QCheckBox, QDialog
from PyQt6.QtCore import QTimer, Qt, QUrl
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
        # ---------------------------------- #

        # ----- NW/Red Spawn Teleport Button ----- #
        red_spawn_teleport_button = QPushButton("NW/Red Spawn Teleport")

        red_spawn_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #red_spawn_teleport_button.setMaximumHeight(50)
        #red_spawn_teleport_button.setMinimumHeight(50)

        red_spawn_teleport_button.clicked.connect(lambda: asyncio.create_task(self.red_spawn_teleport()))

        self.teleports_tab_layout.addWidget(red_spawn_teleport_button)
        # ---------------------------------------- #

        # ----- SW/Blue Spawn Teleport Button ----- #
        blue_spawn_teleport_button = QPushButton("SW/Blue Spawn Teleport")

        blue_spawn_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #blue_spawn_teleport_button.setMaximumHeight(50)
        #blue_spawn_teleport_button.setMinimumHeight(50)

        blue_spawn_teleport_button.clicked.connect(lambda: asyncio.create_task(self.blue_spawn_teleport()))

        self.teleports_tab_layout.addWidget(blue_spawn_teleport_button)
        # ---------------------------------------- #

        # ----- NE/Green Spawn Teleport Button ----- #
        green_spawn_teleport_button = QPushButton("NE/Green Spawn Teleport")

        green_spawn_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #green_spawn_teleport_button.setMaximumHeight(50)
        #green_spawn_teleport_button.setMinimumHeight(50)

        green_spawn_teleport_button.clicked.connect(lambda: asyncio.create_task(self.green_spawn_teleport()))

        self.teleports_tab_layout.addWidget(green_spawn_teleport_button)
        # ----------------------------------------- #

        # ----- SE/Green Spawn Teleport Button ----- #
        purple_spawn_teleport_button = QPushButton("SE/Purple Spawn Teleport")

        purple_spawn_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #purple_spawn_teleport_button.setMaximumHeight(50)
        #purple_spawn_teleport_button.setMinimumHeight(50)

        purple_spawn_teleport_button.clicked.connect(lambda: asyncio.create_task(self.purple_spawn_teleport()))

        self.teleports_tab_layout.addWidget(purple_spawn_teleport_button)
        # ----------------------------------------- #

    async def red_spawn_teleport(self):
        print(f"[TELEPORTS] NW/Red Spawn Teleport pressed.")

        await self.utils.handle_basic_teleport(-15055.607, 31933.933, 1501.999)

    async def blue_spawn_teleport(self):
        print(f"[TELEPORTS] SW/Blue Spawn Teleport pressed.")

        await self.utils.handle_basic_teleport(-13815.256, 8860.154, 2.000)

    async def green_spawn_teleport(self):
        print(f"[TELEPORTS] SW/Green Spawn Teleport pressed.")

        await self.utils.handle_basic_teleport(15521.919, 31776.859, 1501.999)

    async def purple_spawn_teleport(self):
        print(f"[TELEPORTS] SE/Purple Spawn Teleport pressed.")

        await self.utils.handle_basic_teleport(13955.243, 7032.375, 2.000)

class CatapultsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients
        self.catapult_task = None

        # ----- Creating Layout ----- #
        self.catapults_tab_layout = QVBoxLayout()
        self.setLayout(self.catapults_tab_layout)
        # --------------------------- #

        # ----- Creating Ropes Group ----- #
        self.ropes_group = QGroupBox("Ropes")
        self.ropes_group_layout = QHBoxLayout()
        # -------------------------------- #

        # ----- Creating Catapults Group ----- #
        self.catapults_group = QGroupBox("Catapults")
        self.catapults_group_layout = QVBoxLayout()
        # ------------------------------------ #

        # ----- Rope Teleport Button ----- #
        rope_teleport_button = QPushButton("Rope Teleport")

        rope_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        # rope_teleport_button.setMaximumHeight(50)
        # rope_teleport_button.setMinimumHeight(50)

        rope_teleport_button.clicked.connect(lambda: asyncio.create_task(self.rope_teleport()))

        self.ropes_group_layout.addWidget(rope_teleport_button)
        # -------------------------------- #

        # ----- Grab Rope Button ----- #
        grab_rope_button = QPushButton("Grab Rope")

        grab_rope_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        # grab_rope_button.setMaximumHeight(50)
        # grab_rope_button.setMinimumHeight(50)

        grab_rope_button.clicked.connect(lambda: asyncio.create_task(self.grab_rope()))

        self.ropes_group_layout.addWidget(grab_rope_button)
        # ----------------------------- #

        # ----- Fix NW/Red Catapult Button ----- #
        fix_red_catapult_button = QPushButton("Fix NW/Red Catapult")

        fix_red_catapult_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        # fix_red_catapult_button.setMaximumHeight(50)
        # fix_red_catapult_button.setMinimumHeight(50)

        fix_red_catapult_button.clicked.connect(lambda: asyncio.create_task(self.fix_red_catapult_button()))

        self.catapults_group_layout.addWidget(fix_red_catapult_button)
        # ------------------------------------- #

        # ----- Fix SW/Blue Catapult Button ----- #
        fix_blue_catapult_button = QPushButton("Fix SW/Blue Catapult")

        fix_blue_catapult_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        # fix_blue_catapult_button.setMaximumHeight(50)
        # fix_blue_catapult_button.setMinimumHeight(50)

        fix_blue_catapult_button.clicked.connect(lambda: asyncio.create_task(self.fix_blue_catapult_button()))

        self.catapults_group_layout.addWidget(fix_blue_catapult_button)
        # --------------------------------------- #

        # ----- Fix NE/Green Catapult Button ----- #
        fix_green_catapult_button = QPushButton("Fix NE/Green Catapult")

        fix_green_catapult_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        # fix_green_catapult_button.setMaximumHeight(50)
        # fix_green_catapult_button.setMinimumHeight(50)

        fix_green_catapult_button.clicked.connect(lambda: asyncio.create_task(self.fix_green_catapult_button()))

        self.catapults_group_layout.addWidget(fix_green_catapult_button)
        # --------------------------------------- #

        # ----- Fix SE/Purple Catapult Button ----- #
        fix_purple_catapult_button = QPushButton("Fix SE/Purple Catapult")

        fix_purple_catapult_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        # fix_purple_catapult_button.setMaximumHeight(50)
        # fix_purple_catapult_button.setMinimumHeight(50)

        fix_purple_catapult_button.clicked.connect(lambda: asyncio.create_task(self.fix_purple_catapult_button()))

        self.catapults_group_layout.addWidget(fix_purple_catapult_button)
        # ----------------------------------------- #

        self.ropes_group.setLayout(self.ropes_group_layout)
        self.catapults_group.setLayout(self.catapults_group_layout)

        self.catapults_tab_layout.addWidget(self.ropes_group)
        self.catapults_tab_layout.addWidget(self.catapults_group)

    async def rope_teleport(self):
        print(f"[CATAPULTS] Rope Teleport pressed.")

        await self.utils.entity_teleport("Raid-PL-Gear")

    async def grab_rope(self):
        print(f"[CATAPULTS] Grab Rope pressed.")

        await self.utils.grab_item("Raid-PL-Gear")

    async def fix_red_catapult_button(self):
        print(f"[CATAPULTS] Fix NW/Red Catapult pressed.")

        if not self.catapult_task:
            self.catapult_task = asyncio.create_task(self.utils.fix_catapult(-14718.865, 31162.017, 1501.999))
            return
        
        if self.catapult_task:
            self.catapult_task.cancel()
            self.catapult_task = None

    async def fix_blue_catapult_button(self):
        print(f"[CATAPULTS] Fix SW/Blue Catapult pressed.")

        if not self.catapult_task:
            self.catapult_task = asyncio.create_task(self.utils.fix_catapult(-13117.941, 7894.646, 3.100))
            return
        
        if self.catapult_task:
            self.catapult_task.cancel()
            self.catapult_task = None

    async def fix_green_catapult_button(self):
        print(f"[CATAPULTS] Fix NW/Green Catapult pressed.")

        if not self.catapult_task:
            self.catapult_task = asyncio.create_task(self.utils.fix_catapult(14635.608, 30463.625, 1501.999))
            return
        
        if self.catapult_task:
            self.catapult_task.cancel()
            self.catapult_task = None

    async def fix_purple_catapult_button(self):
        print(f"[CATAPULTS] Fix SE/Purple Catapult pressed.")

        if not self.catapult_task:
            self.catapult_task = asyncio.create_task(self.utils.fix_catapult(13085.874, 7782.641, 3.100))
            return
        
        if self.catapult_task:
            self.catapult_task.cancel()
            self.catapult_task = None

class CannonsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.cannons_tab_layout = QVBoxLayout()
        self.setLayout(self.cannons_tab_layout)
        # --------------------------- #

        # ----- Creating Cannonballs Group ----- #
        self.cannonballs_group = QGroupBox("Cannonballs")
        self.cannonballs_group_layout = QHBoxLayout()
        # ---------------------------------- #

        # ----- Creating Cannons Group ----- #
        self.cannons_group = QGroupBox("Cannons")
        self.cannons_group_layout = QHBoxLayout()
        # ---------------------------------- #

        # ----- East Cannonball Teleport Button ----- #
        east_cannonball_teleport_button = QPushButton("East Cannonball Teleport")

        east_cannonball_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #east_cannonball_teleport_button.setMaximumHeight(50)
        #east_cannonball_teleport_button.setMinimumHeight(50)

        east_cannonball_teleport_button.clicked.connect(lambda: asyncio.create_task(self.east_cannonball_teleport()))

        self.cannonballs_group_layout.addWidget(east_cannonball_teleport_button)
        # -------------------------------- #

        # ----- West Cannonball Teleport Button ----- #
        west_cannonball_teleport_button = QPushButton("West Cannonball Teleport")

        west_cannonball_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #west_cannonball_teleport_button.setMaximumHeight(50)
        #west_cannonball_teleport_button.setMinimumHeight(50)

        west_cannonball_teleport_button.clicked.connect(lambda: asyncio.create_task(self.west_cannonball_teleport()))

        self.cannonballs_group_layout.addWidget(west_cannonball_teleport_button)
        # -------------------------------- #

        # ----- East Cannon Teleport Button ----- #
        east_cannon_teleport_button = QPushButton("East Cannon Teleport")

        east_cannon_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #east_cannon_teleport_button.setMaximumHeight(50)
        #east_cannon_teleport_button.setMinimumHeight(50)

        east_cannon_teleport_button.clicked.connect(lambda: asyncio.create_task(self.east_cannon_teleport()))

        self.cannons_group_layout.addWidget(east_cannon_teleport_button)
        # -------------------------------- #

        # ----- West Cannon Teleport Button ----- #
        west_cannon_teleport_button = QPushButton("West Cannon Teleport")

        west_cannon_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #west_cannon_teleport_button.setMaximumHeight(50)
        #west_cannon_teleport_button.setMinimumHeight(50)

        west_cannon_teleport_button.clicked.connect(lambda: asyncio.create_task(self.west_cannon_teleport()))

        self.cannons_group_layout.addWidget(west_cannon_teleport_button)
        # -------------------------------- #

        self.cannonballs_group.setLayout(self.cannonballs_group_layout)
        self.cannons_group.setLayout(self.cannons_group_layout)

        self.cannons_tab_layout.addWidget(self.cannonballs_group)
        self.cannons_tab_layout.addWidget(self.cannons_group)

    async def east_cannonball_teleport(self):
        print(f"[CANNONS] East Cannonball Teleport pressed.")

        await self.utils.handle_basic_teleport(8337.384, 4979.809, -443.177)

    async def west_cannonball_teleport(self):
        print(f"[CANNONS] West Cannonball Teleport pressed.")

        await self.utils.handle_basic_teleport(-8294.083, 5142.723, -449.186)

    async def east_cannon_teleport(self):
        print(f"[CANNONS] East Cannon Teleport pressed.")

        await self.utils.handle_basic_teleport(17986.904, 18609.697, 1002.000)

    async def west_cannon_teleport(self):
        print(f"[CANNONS] West Cannon Teleport pressed.")

        await self.utils.handle_basic_teleport(-17932.748, 18617.435, 1002.000)

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
        # ------------------------------- #

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

        # ----- Polaris Theme Button ----- #
        polaris_theme_button_button = QPushButton("Polaris Theme")

        polaris_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #polaris_theme_button_button.setMaximumHeight(50)
        #polaris_theme_button_button.setMinimumHeight(50)

        polaris_theme_button_button.clicked.connect(self.enable_polaris_theme)

        self.main_themes_group_layout.addWidget(polaris_theme_button_button)
        # -------------------------------- #

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
        # ------------------------------ #

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
        # -------------------------------- #

        self.main_themes_group.setLayout(self.main_themes_group_layout)
        self.preset_themes_group.setLayout(self.preset_themes_group_layout)

        self.themes_tab_layout.addWidget(self.main_themes_group)
        self.themes_tab_layout.addWidget(self.preset_themes_group)

    def enable_default_theme(self):
        print(f"[THEMES] Default theme enabled.")

        self.window().setStyleSheet(self.themes.default)

    def enable_polaris_theme(self):
        print(f"[THEMES] Polaris theme enabled.")

        self.window().setStyleSheet(self.themes.polaris)

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
            self.window().setStyleSheet(self.themes.polaris)

        self.setWindowTitle("Cabal's Revenge Cheat Tool - Lxghtend")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North) # Changes tab position, North: Top, South: Bottom, West: Left, East: Right

        self.hooks_tab = HooksTab(self.utils, self.hooked_clients)
        if self.enable_clients_tab:
            self.clients_tab = ClientsTab(self.utils, self.hooked_clients)
        self.teleports_tab = TeleportsTab(self.utils, self.hooked_clients)
        self.catapults_tab = CatapultsTab(self.utils, self.hooked_clients)
        self.cannons_tab = CannonsTab(self.utils, self.hooked_clients)
        self.utility_tab = UtilityTab(self.utils, self.hooked_clients)
        self.themes_tab = ThemesTab(self.themes)

        tabs.addTab(self.hooks_tab, "Hooks")
        if self.enable_clients_tab:
            tabs.addTab(self.clients_tab, "Clients")
        tabs.addTab(self.teleports_tab, "Teleports")
        tabs.addTab(self.catapults_tab, "Catapults")
        tabs.addTab(self.cannons_tab, "Cannons")
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
        self.setFixedSize(200, 150)
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
    
    app.setStyle("Fusion")

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