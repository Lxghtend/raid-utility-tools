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
        # ------------------------------------ #

        # ----- Mana Ranch Teleport Button ----- #
        mana_ranch_teleport_button = QPushButton("Mana Ranch Teleport")

        mana_ranch_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #mana_ranch_button.setMaximumHeight(50)
        #mana_ranch_button.setMinimumHeight(50)

        mana_ranch_teleport_button.clicked.connect(lambda: asyncio.create_task(self.mana_ranch_teleport()))

        self.teleports_tab_layout.addWidget(mana_ranch_teleport_button)
        # ------------------------------------ #

        # ----- Health Haven Teleport Button ----- #
        health_haven_teleport_button = QPushButton("Health Haven Teleport")

        health_haven_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #health_haven_teleport_button.setMaximumHeight(50)
        #health_haven_teleport_button.setMinimumHeight(50)

        health_haven_teleport_button.clicked.connect(lambda: asyncio.create_task(self.health_haven_teleport()))

        self.teleports_tab_layout.addWidget(health_haven_teleport_button)
        # --------------------------------------- #

        # ----- Minion Ranch Teleport Button ----- #
        minion_ranch_teleport_button = QPushButton("Minion Ranch Teleport")

        minion_ranch_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #minion_ranch_teleport_button.setMaximumHeight(50)
        #minion_ranch_teleport_button.setMinimumHeight(50)

        minion_ranch_teleport_button.clicked.connect(lambda: asyncio.create_task(self.minion_ranch_teleport()))

        self.teleports_tab_layout.addWidget(minion_ranch_teleport_button)
        # --------------------------------------- #

        # ----- Thundering Elf Teleport Button ----- #
        thundering_elf_teleport_button = QPushButton("Thundering Elf Teleport")

        thundering_elf_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #thundering_elf_teleport_button.setMaximumHeight(50)
        #thundering_elf_teleport_button.setMinimumHeight(50)

        thundering_elf_teleport_button.clicked.connect(lambda: asyncio.create_task(self.thundering_elf_teleport()))

        self.teleports_tab_layout.addWidget(thundering_elf_teleport_button)
        # ----------------------------------------- #

        # ----- Millispeeder Teleport Button ----- #
        millispeeder_teleport_button = QPushButton("Millispeeder Teleport")

        millispeeder_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #millispeeder_elf_teleport_button.setMaximumHeight(50)
        #millispeeder_teleport_button.setMinimumHeight(50)

        millispeeder_teleport_button.clicked.connect(lambda: asyncio.create_task(self.millispeeder_teleport()))

        self.teleports_tab_layout.addWidget(millispeeder_teleport_button)
        # ---------------------------------------- #

    async def mana_ranch_teleport(self):
        print("[TELEPORTS] Mana Ranch Teleport pressed.")
        
        await self.utils.handle_basic_teleport(7850.18017578125, 11077.51953125, 30.008514404296875)

    async def health_haven_teleport(self):
        print("[TELEPORTS] Health Haven Teleport pressed.")
        
        await self.utils.handle_basic_teleport(7455.451, 18863.962, 30.008)

    async def minion_ranch_teleport(self):
        print("[TELEPORTS] Minion Ranch Teleport pressed.")

        await self.utils.handle_basic_teleport(16222.608, 26478.230, 39.994)

    async def thundering_elf_teleport(self):
        print("[TELEPORTS] Thundering Elf Teleport pressed.")
        
        await self.utils.handle_basic_teleport(-109.602, 19715.574, -420.011, yaw=1.381)

    async def millispeeder_teleport(self):
        print("[TELEPORTS] Millispeeder Teleport pressed.")

        await self.utils.handle_basic_teleport(22491.021, 26035.205, 30.010)

class StarsTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.chests_tab_layout = QVBoxLayout()
        self.setLayout(self.chests_tab_layout)
        # --------------------------- #

        # ----- Creating Chest Group ----- #
        self.chests_group = QGroupBox("Chests")
        self.chests_group_layout = QHBoxLayout()
        # -------------------------------- #

        # ----- Creating Stars Group ----- #
        self.stars_group = QGroupBox("Stars")
        self.stars_group_layout = QVBoxLayout()
        # -------------------------------- #

        # ----- Mana Chest Button ----- #
        mana_chest_button = QPushButton("Mana Chest Teleport")

        mana_chest_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #mana_chest_button.setMaximumHeight(50)
        #mana_chest_button.setMinimumHeight(50)

        mana_chest_button.clicked.connect(lambda: asyncio.create_task(self.mana_chest_teleport()))

        self.chests_group_layout.addWidget(mana_chest_button)
        # ----------------------------- #

        # ----- Health Chest Button ----- #
        health_chest_button = QPushButton("Health Chest Teleport")

        health_chest_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #health_chest_button.setMaximumHeight(50)
        #health_chest_button.setMinimumHeight(50)

        health_chest_button.clicked.connect(lambda: asyncio.create_task(self.health_chest_teleport()))

        self.chests_group_layout.addWidget(health_chest_button)
        # ------------------------------- #

        # ----- Speed Chest Button ----- #
        speed_chest_button = QPushButton("Speed Chest Teleport")

        speed_chest_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        #speed_chest_button.setMaximumHeight(50)
        #speed_chest_button.setMinimumHeight(50)

        speed_chest_button.clicked.connect(lambda: asyncio.create_task(self.speed_chest_teleport()))

        self.chests_group_layout.addWidget(speed_chest_button)
        # ----------------------------- #

        # ----- Star Teleport Button ----- #
        star_teleport_button = QPushButton("Star Teleport")

        star_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        star_teleport_button.setMaximumHeight(100)
        star_teleport_button.setMinimumHeight(100)

        star_teleport_button.clicked.connect(lambda: asyncio.create_task(self.star_teleport()))

        self.stars_group_layout.addWidget(star_teleport_button)
        # ----------------------------- #
        
        # ----- Grab Star Button ----- #
        grab_star_button = QPushButton("Grab Star")

        grab_star_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        grab_star_button.setMaximumHeight(100)
        grab_star_button.setMinimumHeight(100)

        grab_star_button.clicked.connect(lambda: asyncio.create_task(self.grab_star()))

        self.stars_group_layout.addWidget(grab_star_button)
        # ------------------------------ #

        self.chests_group.setLayout(self.chests_group_layout)
        self.stars_group.setLayout(self.stars_group_layout)

        self.chests_tab_layout.addWidget(self.chests_group)
        self.chests_tab_layout.addWidget(self.stars_group)

    async def mana_chest_teleport(self):
        print(f"[STARS] Mana Chest Teleport pressed.")

        await self.utils.handle_basic_teleport(9956.513671875, 8900.72265625, 120.01296997070312, yaw=2.375)

    async def health_chest_teleport(self):
        print(f"[STARS] Health Chest Teleport pressed.")

        await self.utils.handle_basic_teleport(9747.107421875, 17028.455078125, 30.01165771484375, yaw=5.385)

    async def speed_chest_teleport(self):
        print(f"[STARS] Speed Chest Teleport pressed.")

        await self.utils.handle_basic_teleport(16229.8505859375, 26573.478515625, 39.994598388671875, yaw=2.421)

    async def star_teleport(self):
        print(f"[STARS] Star Teleport pressed.")

        await self.utils.entity_teleport("Raid_PowerSource")

    async def grab_star(self):
        print(f"[STARS] Grab Star pressed.")

        await asyncio.wait_for(self.utils.grab_item("Raid_PowerSource"), timeout=5.0)

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
        # ---------------------------------- #

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
            await self.auto_drums_task

            self.auto_drums_task = None
            return
        
        if self.auto_drums_task:
            self.auto_drums_task.cancel()
            self.auto_drums_task = None

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

        # ----- Dragonspyre Theme Button ----- #
        dragonspyre_theme_button_button = QPushButton("Dragonsypre Theme")

        dragonspyre_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        #dragonspyre_theme_button_button.setMaximumHeight(50)
        #dragonspyre_theme_button_button.setMinimumHeight(50)

        dragonspyre_theme_button_button.clicked.connect(self.enable_dragonspyre_theme)

        self.main_themes_group_layout.addWidget(dragonspyre_theme_button_button)
        # ------------------------------------ #

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
        # ---------------------------- #

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
        # -------------------------------- #

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
        # ------------------------------ #

        self.main_themes_group.setLayout(self.main_themes_group_layout)
        self.preset_themes_group.setLayout(self.preset_themes_group_layout)

        self.themes_tab_layout.addWidget(self.main_themes_group)
        self.themes_tab_layout.addWidget(self.preset_themes_group)

    def enable_default_theme(self):
        print(f"[THEMES] Default theme enabled.")

        self.window().setStyleSheet(self.themes.default)

    def enable_dragonspyre_theme(self):
        print(f"[THEMES] Dragonsypre theme enabled.")

        self.window().setStyleSheet(self.themes.dragonspyre)

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
            self.window().setStyleSheet(self.themes.dragonspyre)

        self.setWindowTitle("Voracious Void Cheat Tool - Lxghtend")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North) # Changes tab position, North: Top, South: Bottom, West: Left, East: Right

        self.hooks_tab = HooksTab(self.utils, self.hooked_clients)
        if self.enable_clients_tab:
            self.clients_tab = ClientsTab(self.utils, self.hooked_clients)
        self.teleports_tab = TeleportsTab(self.utils, self.hooked_clients)
        self.stars_tab = StarsTab(self.utils, self.hooked_clients)
        self.drums_tab = DrumsTab(self.utils, self.hooked_clients)
        self.utility_tab = UtilityTab(self.utils, self.hooked_clients)
        self.themes_tab = ThemesTab(self.themes)

        tabs.addTab(self.hooks_tab, "Hooks")
        if self.enable_clients_tab:
            tabs.addTab(self.clients_tab, "Clients")
        tabs.addTab(self.teleports_tab, "Teleports")
        tabs.addTab(self.stars_tab, "Stars")
        tabs.addTab(self.drums_tab, "Drums")
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
        self.setFixedSize(220, 150)
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