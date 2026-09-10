import asyncio
import ctypes
import json
import os
import sys

import keyboard
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qasync import QEventLoop
from themes import Themes
from utils import Utils

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared")
)
from tracking import send_ping
from updater import check_for_update, trigger_update


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

        # rename_clients_button.setMaximumHeight(50)
        rename_clients_button.setMinimumHeight(50)

        rename_clients_button.clicked.connect(
            lambda: asyncio.create_task(self.rename_clients_wrapper())
        )

        self.hooks_tab_layout.addWidget(rename_clients_button)
        # --------------------------------- #

        self.hooks_tab_layout.addStretch()  # makes rename button go to top

        # ----- Available Clients Checkboxes ----- #
        self.hooks_checkboxes = QGroupBox("Available Clients")
        self.hooks_checkboxes_layout = QVBoxLayout()

        self.client_checkboxes = []
        QTimer.singleShot(
            0, lambda: asyncio.create_task(self.update_client_checkboxes())
        )

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
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # activate_hooks_button.setMaximumHeight(50)
        activate_hooks_button.setMinimumHeight(50)

        activate_hooks_button.clicked.connect(
            lambda: asyncio.create_task(self.activate_hooks_wrapper())
        )

        self.hooks_tab_layout.addWidget(activate_hooks_button)
        # --------------------------------- #

        # ----- Deactivate Hooks Button ----- #
        deactivate_hooks_button = QPushButton("Deactivate Hooks")

        deactivate_hooks_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # deactivate_hooks_button.setMaximumHeight(50)
        deactivate_hooks_button.setMinimumHeight(50)

        deactivate_hooks_button.clicked.connect(
            lambda: asyncio.create_task(self.deactivate_hooks_wrapper())
        )

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

        await asyncio.gather(
            *[(self.utils.activate_hooks(client)) for client in clients_to_hook]
        )

        for client in clients_to_hook:
            if client.process_id not in {
                hooked_client.process_id for hooked_client in self.hooked_clients
            }:
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
            existing_processes = [
                client_checkbox.property("client").process_id
                for client_checkbox in self.client_checkboxes
            ]

            # Remove Client Checkboxes that don't exist
            for client_checkbox in self.client_checkboxes[:]:
                if client_checkbox.property("client").process_id not in [
                    client.process_id for client in clients
                ]:
                    self.hooks_checkboxes_layout.removeWidget(client_checkbox)
                    client_checkbox.deleteLater()

                    self.client_checkboxes.remove(client_checkbox)

            for client_checkbox in self.client_checkboxes:
                client_process_id = client_checkbox.property(
                    "client"
                ).process_id  # process id that is stored
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

        QTimer.singleShot(
            0, lambda: asyncio.create_task(self.update_hooked_client_info())
        )

    async def update_hooked_client_info(self):
        while True:
            # Remove clients that are no longer hooked
            for client_process_id in list(self.client_frames.keys()):
                if all(
                    client_process_id != client.process_id
                    for client in self.hooked_clients
                ):  # unreadable, i know
                    client_frame_info = self.client_frames.pop(client_process_id)
                    client_frame = client_frame_info["frame"]
                    self.clients_tab_layout.removeWidget(client_frame)
                    client_frame.deleteLater()

            # Add new hooked clients
            for client in self.hooked_clients:
                if client.process_id not in self.client_frames:
                    client_frame = QGroupBox(client.title)
                    client_frame_layout = QVBoxLayout()

                    level_label = QLabel(
                        f"Level: {await client.stats.reference_level()}"
                    )
                    health_label = QLabel(
                        f"Health: {await client.stats.current_hitpoints()}/{await client.stats.max_hitpoints()}"
                    )
                    mana_label = QLabel(
                        f"Mana: {await client.stats.current_mana()}/{await client.stats.max_mana()}"
                    )
                    energy_label = QLabel(
                        f"Energy: {await client.current_energy()}/{await client.stats.energy_max() + await client.stats.bonus_energy()}"
                    )
                    position_label = QLabel(f"Position: {await client.body.position()}")
                    yaw_label = QLabel(f"Yaw: {await client.body.yaw()}")

                    client_frame_layout.addWidget(level_label)
                    client_frame_layout.addWidget(health_label)
                    client_frame_layout.addWidget(mana_label)
                    client_frame_layout.addWidget(energy_label)
                    client_frame_layout.addWidget(position_label)
                    client_frame_layout.addWidget(yaw_label)

                    self.client_frames[client.process_id] = {
                        "frame": client_frame,
                        "labels": {
                            "level": level_label,
                            "health": health_label,
                            "mana": mana_label,
                            "energy": energy_label,
                            "position": position_label,
                            "yaw": yaw_label,
                        },
                    }

                    client_frame.setLayout(client_frame_layout)

                    # self.client_frames[client.title] = client_frame # sets the key (title) to the frame
                    self.clients_tab_layout.addWidget(
                        client_frame, alignment=Qt.AlignmentFlag.AlignTop
                    )

                else:
                    client_labels = self.client_frames[client.process_id]["labels"]
                    client_labels["level"].setText(
                        f"Level: {await client.stats.reference_level()}"
                    )
                    client_labels["health"].setText(
                        f"Health: {await client.stats.current_hitpoints()}/{await client.stats.max_hitpoints()}"
                    )
                    client_labels["mana"].setText(
                        f"Mana: {await client.stats.current_mana()}/{await client.stats.max_mana()}"
                    )
                    client_labels["energy"].setText(
                        f"Energy: {await client.current_energy()}/{await client.stats.energy_max() + await client.stats.bonus_energy()}"
                    )
                    client_labels["position"].setText(
                        f"Position: {await client.body.position()}"
                    )
                    client_labels["yaw"].setText(f"Yaw: {await client.body.yaw()}")

            await asyncio.sleep(1)


class KeysTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.keys_tab_layout = QVBoxLayout()
        self.setLayout(self.keys_tab_layout)
        # --------------------------- #

        # ----- Creating Keys Group ----- #
        self.keys_group = QGroupBox("Keys")
        self.keys_group_layout = QHBoxLayout()
        # -------------------------------- #

        # ----- Creating Doors Group ----- #
        self.doors_group = QGroupBox("Doors")
        self.doors_group_layout = QVBoxLayout()

        self.doors_row_top = QHBoxLayout()
        self.doors_group_layout.addLayout(self.doors_row_top)

        self.doors_row_bottom = QHBoxLayout()
        self.doors_group_layout.addLayout(self.doors_row_bottom)
        # -------------------------------- #

        # ----- First Floor Button ----- #
        first_floor_button = QPushButton("First Floor")

        first_floor_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        first_floor_button.clicked.connect(
            lambda: asyncio.create_task(self.first_floor_teleport())
        )

        self.keys_group_layout.addWidget(first_floor_button)
        # ----------------------------- #

        # ----- Second Floor Button ----- #
        second_floor_button = QPushButton("Second Floor")

        second_floor_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        second_floor_button.clicked.connect(
            lambda: asyncio.create_task(self.second_floor_teleport())
        )

        self.keys_group_layout.addWidget(second_floor_button)
        # ------------------------------- #

        # ----- Grab Key Button ----- #
        key_button = QPushButton("Grab Key")

        key_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        key_button.clicked.connect(lambda: asyncio.create_task(self.grab_key()))

        self.keys_group_layout.addWidget(key_button)
        # ----------------------------- #

        # ----- Infernal Oni Button ----- #
        infernal_oni_button = QPushButton("Infernal Oni")

        infernal_oni_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        infernal_oni_button.clicked.connect(
            lambda: asyncio.create_task(self.infernal_oni_teleport())
        )

        self.doors_row_top.addWidget(infernal_oni_button)
        # -------------------------------- #

        # ----- Turmoil Oni Button ----- #
        turmoil_oni_button = QPushButton("Turmoil Oni")

        turmoil_oni_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        turmoil_oni_button.clicked.connect(
            lambda: asyncio.create_task(self.turmoil_oni_teleport())
        )

        self.doors_row_top.addWidget(turmoil_oni_button)
        # ----------------------------- #

        # ----- Everwinter Oni Button ----- #
        everwinter_oni_button = QPushButton("Everwinter Oni")

        everwinter_oni_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        everwinter_oni_button.clicked.connect(
            lambda: asyncio.create_task(self.everwinter_oni_teleport())
        )

        self.doors_row_top.addWidget(everwinter_oni_button)
        # ----------------------------- #

        # ----- Doom Oni Button ----- #
        doom_oni_button = QPushButton("Doom Oni")

        doom_oni_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        doom_oni_button.clicked.connect(
            lambda: asyncio.create_task(self.doom_oni_teleport())
        )

        self.doors_row_bottom.addWidget(doom_oni_button)
        # ------------------------------ #

        # ----- Trickster Oni Button ----- #
        trickster_oni_button = QPushButton("Trickster Oni")

        trickster_oni_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        trickster_oni_button.clicked.connect(
            lambda: asyncio.create_task(self.trickster_oni_teleport())
        )

        self.doors_row_bottom.addWidget(trickster_oni_button)
        # ----------------------------- #

        # ----- Primal Oni Button ----- #
        primal_oni_button = QPushButton("Primal Oni")

        primal_oni_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        primal_oni_button.clicked.connect(
            lambda: asyncio.create_task(self.primal_oni_teleport())
        )

        self.doors_row_bottom.addWidget(primal_oni_button)
        # ----------------------------- #

        self.keys_group.setLayout(self.keys_group_layout)
        self.doors_group.setLayout(self.doors_group_layout)

        self.keys_tab_layout.addWidget(self.keys_group, 1)
        self.keys_tab_layout.addWidget(self.doors_group, 2)

    async def first_floor_teleport(self):
        print(f"[KEY] First Floor Teleport pressed.")

        await self.utils.handle_basic_teleport(52620.828, 46.415, -10625.969)  # jz

    async def second_floor_teleport(self):
        print(f"[KEY] Second Floor Teleport pressed.")

        await self.utils.handle_basic_teleport(-55400.0, 300.0, -5123.629)  # ratul

    async def grab_key(self):
        print(f"[KEY] Grab Key pressed.")

        await self.utils.grab_item("Raid_MS_Door_Key_01")

    async def infernal_oni_teleport(self):
        print(f"[ONI] Infernal Oni Teleport pressed.")

        await self.utils.handle_basic_teleport(55500.0, -4250.0, -10625.966)  # ratul

    async def turmoil_oni_teleport(self):
        print(f"[ONI] Turmoil Oni Teleport pressed.")

        await self.utils.handle_basic_teleport(52600.0, 750.0, -10625.967)  # ratul

    async def everwinter_oni_teleport(self):
        print(f"[ONI] Everwinter Oni Teleport pressed.")

        await self.utils.handle_basic_teleport(49750.0, -4325.0, -10625.965)  # ratul

    async def doom_oni_teleport(self):
        print(f"[ONI] Doom Oni Teleport pressed.")

        await self.utils.handle_basic_teleport(49750.0, -850.0, -10625.967)  # ratul

    async def trickster_oni_teleport(self):
        print(f"[ONI] Trickster Oni Teleport pressed.")

        await self.utils.handle_basic_teleport(52600.0, -5950.0, -10625.967)  # ratul

    async def primal_oni_teleport(self):
        print(f"[ONI] Primal Oni Teleport pressed.")

        await self.utils.handle_basic_teleport(55500.0, -750.0, -10625.966)  # ratul


class DryadTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.dryad_tab_layout = QVBoxLayout()
        self.setLayout(self.dryad_tab_layout)
        # --------------------------- #

        # ----- Creating Seeds Group ----- #
        self.seeds_group = QGroupBox("Seeds")
        self.seeds_group_layout = QHBoxLayout()

        self.left_seeds_column = QVBoxLayout()
        self.seeds_group_layout.addLayout(self.left_seeds_column)

        self.right_seeds_column = QVBoxLayout()
        self.seeds_group_layout.addLayout(self.right_seeds_column)
        # -------------------------------- #

        # ----- Creating Dryads Group ----- #
        self.dryads_group = QGroupBox("Dryads")
        self.dryads_group_layout = QHBoxLayout()

        self.left_dryads_column = QVBoxLayout()
        self.dryads_group_layout.addLayout(self.left_dryads_column)

        self.right_dryads_column = QVBoxLayout()
        self.dryads_group_layout.addLayout(self.right_dryads_column)
        # --------------------------------- #

        # ----- Creating Braziers Group ----- #
        self.braziers_group = QGroupBox("Braziers")
        self.braziers_group_layout = QHBoxLayout()
        # ----------------------------------- #

        # ----- Infernal Seed Button ----- #
        infernal_seed_button = QPushButton("Infernal Seed")

        infernal_seed_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        infernal_seed_button.clicked.connect(
            lambda: asyncio.create_task(self.infernal_seed_teleport())
        )

        self.left_seeds_column.addWidget(infernal_seed_button)
        # -------------------------------- #

        # ----- Turmoil Seed Button ----- #
        turmoil_seed_button = QPushButton("Turmoil Seed")

        turmoil_seed_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        turmoil_seed_button.clicked.connect(
            lambda: asyncio.create_task(self.turmoil_seed_teleport())
        )

        self.left_seeds_column.addWidget(turmoil_seed_button)
        # ------------------------------- #

        # ----- Everwinter Seed Button ----- #
        everwinter_seed_button = QPushButton("Everwinter Seed")

        everwinter_seed_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        everwinter_seed_button.clicked.connect(
            lambda: asyncio.create_task(self.everwinter_seed_teleport())
        )

        self.left_seeds_column.addWidget(everwinter_seed_button)
        # ---------------------------------- #

        # ----- Doom Seed Button ----- #
        doom_seed_button = QPushButton("Doom Seed")

        doom_seed_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        doom_seed_button.clicked.connect(
            lambda: asyncio.create_task(self.doom_seed_teleport())
        )

        self.right_seeds_column.addWidget(doom_seed_button)
        # ---------------------------- #

        # ----- Trickster Seed Button ----- #
        trickster_seed_button = QPushButton("Trickster Seed")

        trickster_seed_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        trickster_seed_button.clicked.connect(
            lambda: asyncio.create_task(self.trickster_seed_teleport())
        )

        self.right_seeds_column.addWidget(trickster_seed_button)
        # --------------------------------- #

        # ----- Primal Seed Button ----- #
        primal_seed_button = QPushButton("Primal Seed")

        primal_seed_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        primal_seed_button.clicked.connect(
            lambda: asyncio.create_task(self.primal_seed_teleport())
        )

        self.right_seeds_column.addWidget(primal_seed_button)
        # ------------------------------ #

        # ----- Infernal Dryad Teleport Button ----- #
        infernal_dryad_teleport_button = QPushButton("Infernal Dryad Teleport")

        infernal_dryad_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        infernal_dryad_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.infernal_dryad_teleport())
        )

        self.left_dryads_column.addWidget(infernal_dryad_teleport_button)
        # ------------------------------------------ #

        # ----- Turmoil Dryad Teleport Button ----- #
        turmoil_dryad_teleport_button = QPushButton("Turmoil Dryad Teleport")

        turmoil_dryad_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        turmoil_dryad_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.turmoil_dryad_teleport())
        )

        self.left_dryads_column.addWidget(turmoil_dryad_teleport_button)
        # ----------------------------------------- #

        # ----- Everwinter Dryad Teleport Button ----- #
        everwinter_dryad_teleport_button = QPushButton("Everwinter Dryad Teleport")

        everwinter_dryad_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        everwinter_dryad_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.everwinter_dryad_teleport())
        )

        self.left_dryads_column.addWidget(everwinter_dryad_teleport_button)
        # -------------------------------------------- #

        # ----- Doom Dryad Teleport Button ----- #
        doom_dryad_teleport_button = QPushButton("Doom Dryad Teleport")

        doom_dryad_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        doom_dryad_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.doom_dryad_teleport())
        )

        self.right_dryads_column.addWidget(doom_dryad_teleport_button)
        # -------------------------------------- #

        # ----- Trickster Dryad Teleport Button ----- #
        trickster_dryad_teleport_button = QPushButton("Trickster Dryad Teleport")

        trickster_dryad_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        trickster_dryad_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.trickster_dryad_teleport())
        )

        self.right_dryads_column.addWidget(trickster_dryad_teleport_button)
        # ------------------------------------------- #

        # ----- Primal Dryad Teleport Button ----- #
        primal_dryad_teleport_button = QPushButton("Primal Dryad Teleport")

        primal_dryad_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        primal_dryad_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.primal_dryad_teleport())
        )

        self.right_dryads_column.addWidget(primal_dryad_teleport_button)
        # ---------------------------------------- #

        # ----- Giver of the Time Torch Button ----- #
        giver_of_the_time_torch_button = QPushButton("Giver of the Time Torch")

        giver_of_the_time_torch_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        giver_of_the_time_torch_button.clicked.connect(
            lambda: asyncio.create_task(self.giver_of_the_time_torch())
        )

        self.braziers_group_layout.addWidget(giver_of_the_time_torch_button)
        # ------------------------------------------- #

        # ----- Swifty's Shop Button ----- #
        swiftys_shop_button = QPushButton("Swifty's Shop")

        swiftys_shop_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        swiftys_shop_button.clicked.connect(
            lambda: asyncio.create_task(self.swiftys_shop())
        )

        self.braziers_group_layout.addWidget(swiftys_shop_button)
        # ------------------------------- #

        # ----- VG Mobs Button ----- #
        vg_mobs_button = QPushButton("VG Mobs")

        vg_mobs_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        vg_mobs_button.clicked.connect(
            lambda: asyncio.create_task(self.vg_mobs())
        )

        self.braziers_group_layout.addWidget(vg_mobs_button)
        # -------------------------- #

        self.seeds_group.setLayout(self.seeds_group_layout)
        self.dryads_group.setLayout(self.dryads_group_layout)
        self.braziers_group.setLayout(self.braziers_group_layout)

        self.dryad_tab_layout.addWidget(self.seeds_group, 1)
        self.dryad_tab_layout.addWidget(self.dryads_group, 1)
        self.dryad_tab_layout.addWidget(self.braziers_group)

    async def infernal_seed_teleport(self):
        print(f"[SEED] Infernal Seed Teleport pressed.")

        await self.utils.entity_teleport("GR_MS_Plant_01_Seed")

    async def turmoil_seed_teleport(self):
        print(f"[SEED] Turmoil Seed Teleport pressed.")

        await self.utils.entity_teleport("GR_MS_Plant_03_Seed")

    async def everwinter_seed_teleport(self):
        print(f"[SEED] Everwinter Seed Teleport pressed.")

        await self.utils.entity_teleport("GR_MS_Plant_02_Seed")

    async def doom_seed_teleport(self):
        print(f"[SEED] Doom Seed Teleport pressed.")

        await self.utils.entity_teleport("GR_MS_Plant_06_Seed")

    async def trickster_seed_teleport(self):
        print(f"[SEED] Trickster Seed Teleport pressed.")

        await self.utils.entity_teleport("GR_MS_Plant_04_Seed")

    async def primal_seed_teleport(self):
        print(f"[SEED] Primal Seed Teleport pressed.")

        await self.utils.entity_teleport("GR_MS_Plant_05_Seed")

    async def infernal_dryad_teleport(self):
        print(f"[DRYAD] Infernal Dryad Teleport pressed.")

        await self.utils.handle_basic_teleport(-51750.0, -4750.0, -5122.860) # ratul

    async def turmoil_dryad_teleport(self):
        print(f"[DRYAD] Turmoil Dryad Teleport pressed.")

        await self.utils.handle_basic_teleport(-55500.0, 1850.0, -5122.856) # ratul

    async def everwinter_dryad_teleport(self):
        print(f"[DRYAD] Everwinter Dryad Teleport pressed.")

        await self.utils.handle_basic_teleport(-59250.0, -4750.0, -5122.870) # ratul

    async def doom_dryad_teleport(self):
        print(f"[DRYAD] Doom Dryad Teleport pressed.")

        await self.utils.handle_basic_teleport(-59250.0, -400.0, -5122.860) # ratul

    async def trickster_dryad_teleport(self):
        print(f"[DRYAD] Trickster Dryad Teleport pressed.")

        await self.utils.handle_basic_teleport(-55400.0, -7000.0, -5122.858) # ratul

    async def primal_dryad_teleport(self):
        print(f"[DRYAD] Primal Dryad Teleport pressed.")

        await self.utils.handle_basic_teleport(-51500.0, -350.0, -5122.854) # ratul

    async def giver_of_the_time_torch(self):
        print(f"[BRAZIERS] Giver of the Time Torch pressed.")

        await self.utils.handle_basic_teleport(-54850.0, -4210.0, -5123.630) # ratul

    async def swiftys_shop(self):
        print(f"[BRAZIERS] Swifty's Shop pressed.")

        await self.utils.handle_basic_teleport(-55450.0, -625.0, -5123.629) # ratul

    async def vg_mobs(self):
        print(f"[BRAZIERS] VG Mobs pressed.")

        await self.utils.handle_basic_teleport(-53576.586,  -2544.172,  -5123.632) # jz


class EarlygameTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients
        self.wisp_dialog = None

        # ----- Creating Layout ----- #
        self.earlygame_tab_layout = QVBoxLayout()
        self.setLayout(self.earlygame_tab_layout)
        # --------------------------- #

        # ----- Creating General Group ----- #
        self.general_group = QGroupBox("General")
        self.general_group_layout = QVBoxLayout()

        self.intersection_buttons_row_top = QHBoxLayout()
        self.intersection_buttons_row_bottom = QHBoxLayout()
        # ---------------------------------- #

        # ----- Creating Shrines Group ----- #
        self.shrines_group = QGroupBox("Shrines")
        self.shrines_group_layout = QVBoxLayout()

        self.shrines_row_top = QHBoxLayout()
        self.shrines_group_layout.addLayout(self.shrines_row_top)

        self.shrines_row_bottom = QHBoxLayout()
        self.shrines_group_layout.addLayout(self.shrines_row_bottom)
        # ---------------------------------- #

        # ----- Creating Essence Forges Group ----- #
        self.essence_forges_group = QGroupBox("Essence Forges")
        self.essence_forges_group_layout = QHBoxLayout()
        # ----------------------------------------- #

        # ----- Wisp Teleport Button ----- #
        wisp_teleport_button = QPushButton("Wisp Teleport")

        wisp_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        wisp_teleport_button.setMaximumHeight(50)
        wisp_teleport_button.setMinimumHeight(50)

        wisp_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.wisp_teleport())
        )

        self.general_group_layout.addWidget(wisp_teleport_button)
        # -------------------------------- #

        # ----- North Intersection Button ----- #
        north_intersection_teleport_button = QPushButton("North Intersection")

        north_intersection_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        north_intersection_teleport_button.setMaximumHeight(50)
        north_intersection_teleport_button.setMinimumHeight(50)

        north_intersection_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.north_intersection_teleport())
        )

        self.intersection_buttons_row_top.addWidget(north_intersection_teleport_button)
        # ------------------------------------- #

        # ----- East Intersection Button ----- #
        east_intersection_teleport_button = QPushButton("East Intersection")

        east_intersection_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        east_intersection_teleport_button.setMaximumHeight(50)
        east_intersection_teleport_button.setMinimumHeight(50)

        east_intersection_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.east_intersection_teleport())
        )

        self.intersection_buttons_row_top.addWidget(east_intersection_teleport_button)
        # ------------------------------------ #

        # ----- South Intersection Button ----- #
        south_intersection_teleport_button = QPushButton("South Intersection")

        south_intersection_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        south_intersection_teleport_button.setMaximumHeight(50)
        south_intersection_teleport_button.setMinimumHeight(50)

        south_intersection_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.south_intersection_teleport())
        )

        self.intersection_buttons_row_bottom.addWidget(
            south_intersection_teleport_button
        )
        # ------------------------------------- #

        # ----- West Intersection Button ----- #
        west_intersection_teleport_button = QPushButton("West Intersection")

        west_intersection_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        west_intersection_teleport_button.setMaximumHeight(50)
        west_intersection_teleport_button.setMinimumHeight(50)

        west_intersection_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.west_intersection_teleport())
        )

        self.intersection_buttons_row_bottom.addWidget(
            west_intersection_teleport_button
        )
        # ------------------------------------ #

        self.general_group_layout.addLayout(self.intersection_buttons_row_top)
        self.general_group_layout.addLayout(self.intersection_buttons_row_bottom)

        # ----- Death Shrine Button ----- #
        death_shrine_teleport_button = QPushButton("Death Shrine")

        death_shrine_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        death_shrine_teleport_button.setMaximumHeight(50)
        death_shrine_teleport_button.setMinimumHeight(50)

        death_shrine_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.death_shrine_teleport())
        )

        self.shrines_row_top.addWidget(death_shrine_teleport_button)
        # ------------------------------- #

        # ----- Storm Shrine Button ----- #
        storm_shrine_teleport_button = QPushButton("Storm Shrine")

        storm_shrine_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        storm_shrine_teleport_button.setMaximumHeight(50)
        storm_shrine_teleport_button.setMinimumHeight(50)

        storm_shrine_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.storm_shrine_teleport())
        )

        self.shrines_row_top.addWidget(storm_shrine_teleport_button)
        # ------------------------------- #

        # ----- Life Shrine Button ----- #
        life_shrine_teleport_button = QPushButton("Life Shrine")

        life_shrine_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        life_shrine_teleport_button.setMaximumHeight(50)
        life_shrine_teleport_button.setMinimumHeight(50)

        life_shrine_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.life_shrine_teleport())
        )

        self.shrines_row_top.addWidget(life_shrine_teleport_button)
        # ------------------------------ #

        # ----- Ice Shrine Button ----- #
        ice_shrine_teleport_button = QPushButton("Ice Shrine")

        ice_shrine_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        ice_shrine_teleport_button.setMaximumHeight(50)
        ice_shrine_teleport_button.setMinimumHeight(50)

        ice_shrine_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.ice_shrine_teleport())
        )

        self.shrines_row_bottom.addWidget(ice_shrine_teleport_button)
        # ----------------------------- #

        # ----- Myth Shrine Button ----- #
        myth_shrine_teleport_button = QPushButton("Myth Shrine")

        myth_shrine_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        myth_shrine_teleport_button.setMaximumHeight(50)
        myth_shrine_teleport_button.setMinimumHeight(50)

        myth_shrine_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.myth_shrine_teleport())
        )

        self.shrines_row_bottom.addWidget(myth_shrine_teleport_button)
        # ------------------------------ #

        # ----- Fire Shrine Button ----- #
        fire_shrine_teleport_button = QPushButton("Fire Shrine")

        fire_shrine_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        fire_shrine_teleport_button.setMaximumHeight(50)
        fire_shrine_teleport_button.setMinimumHeight(50)

        fire_shrine_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.fire_shrine_teleport())
        )

        self.shrines_row_bottom.addWidget(fire_shrine_teleport_button)
        # ------------------------------ #

        # ----- North Essence Button ----- #
        north_essence_teleport_button = QPushButton("North Essence")

        north_essence_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        north_essence_teleport_button.setMinimumHeight(50)

        north_essence_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.north_essence_teleport())
        )

        self.essence_forges_group_layout.addWidget(north_essence_teleport_button)
        # -------------------------------- #

        # ----- East Essence Button ----- #
        east_essence_teleport_button = QPushButton("East Essence")

        east_essence_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        east_essence_teleport_button.setMinimumHeight(50)

        east_essence_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.east_essence_teleport())
        )

        self.essence_forges_group_layout.addWidget(east_essence_teleport_button)
        # ------------------------------- #

        # ----- South Essence Button ----- #
        south_essence_teleport_button = QPushButton("South Essence")

        south_essence_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        south_essence_teleport_button.setMinimumHeight(50)

        south_essence_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.south_essence_teleport())
        )

        self.essence_forges_group_layout.addWidget(south_essence_teleport_button)
        # -------------------------------- #

        # ----- West Essence Button ----- #
        west_essence_teleport_button = QPushButton("West Essence")

        west_essence_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        west_essence_teleport_button.setMinimumHeight(50)

        west_essence_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.west_essence_teleport())
        )

        self.essence_forges_group_layout.addWidget(west_essence_teleport_button)
        # ------------------------------- #

        self.general_group.setLayout(self.general_group_layout)
        self.shrines_group.setLayout(self.shrines_group_layout)
        self.essence_forges_group.setLayout(self.essence_forges_group_layout)

        self.earlygame_tab_layout.addWidget(self.general_group)
        self.earlygame_tab_layout.addWidget(self.shrines_group)
        self.earlygame_tab_layout.addWidget(self.essence_forges_group, 1)

    async def wisp_teleport(self):
        print(f"[EARLYGAME] Wisp Teleport pressed.")

        wisps = await self.utils.get_wisps()

        if not wisps:
            return

        def handle_select(wisp):
            if hasattr(self, "wisp_dialog") and self.wisp_dialog:
                self.wisp_dialog.close()
            asyncio.create_task(self.teleport_to_wisp(wisp))

        self.wisp_dialog = WispDialog(
            wisps, on_select=handle_select, parent=self.window()
        )
        self.wisp_dialog.show()

    async def teleport_to_wisp(self, wisp):
        print(f"[EARLYGAME] Teleporting to selected wisp...")

        await self.utils.wisp_teleport(wisp)

    async def north_intersection_teleport(self):
        print(f"[INTERSECTION] North Intersection pressed.")

        await self.utils.handle_basic_teleport(0.0, 5500.0, 210.490) # ratul

    async def east_intersection_teleport(self):
        print(f"[INTERSECTION] East Intersection pressed.")

        await self.utils.handle_basic_teleport(7000.0, -2350.0, 211.516) # ratul

    async def south_intersection_teleport(self):
        print(f"[INTERSECTION] South Intersection pressed.")

        await self.utils.handle_basic_teleport(-1250.0, -10000.0, 211.516) # ratul

    async def west_intersection_teleport(self):
        print(f"[INTERSECTION] West Intersection pressed.")

        await self.utils.handle_basic_teleport(-8000.0, -2300.0, 210.488) # ratul

    async def death_shrine_teleport(self):
        print(f"[SHRINE] Death Shrine pressed.")

        await self.utils.handle_basic_teleport(-11000.0, 2500.0, 229.305) # ratul

    async def storm_shrine_teleport(self):
        print(f"[SHRINE] Storm Shrine pressed.")

        await self.utils.handle_basic_teleport(2000.0, 11200.0, 211.516) # ratul

    async def life_shrine_teleport(self):
        print(f"[SHRINE] Life Shrine pressed.")

        await self.utils.handle_basic_teleport(10000.0, 3500.0, 231.175) # ratul

    async def ice_shrine_teleport(self):
        print(f"[SHRINE] Ice Shrine pressed.")

        await self.utils.handle_basic_teleport(-11000.0, -8000.0, 224.645) # ratul

    async def myth_shrine_teleport(self):
        print(f"[SHRINE] Myth Shrine pressed.")

        await self.utils.handle_basic_teleport(-3000.0, -15900.0, 231.804) # ratul

    async def fire_shrine_teleport(self):
        print(f"[SHRINE] Fire Shrine pressed.")

        await self.utils.handle_basic_teleport(10000.0, -7000.0, 230.445) # ratul

    async def north_essence_teleport(self):
        print(f"[ESSENCE] North Essence pressed.")

        await self.utils.handle_basic_teleport(0.0, 200.0, 204.203) # ratul

    async def east_essence_teleport(self):
        print(f"[ESSENCE] East Essence pressed.")

        await self.utils.handle_basic_teleport(2300.0, -2300.0, 213.011) # ratul

    async def south_essence_teleport(self):
        print(f"[ESSENCE] South Essence pressed.")

        await self.utils.handle_basic_teleport(-1350.0, -5000.0, 207.070) # ratul

    async def west_essence_teleport(self):
        print(f"[ESSENCE] West Essence pressed.")

        await self.utils.handle_basic_teleport(-3600.0, -2300.0, 211.996) # ratul


class EndgameTab(QWidget):
    def __init__(self, utils: Utils, hooked_clients: list):
        super().__init__()
        self.utils = utils
        self.hooked_clients = hooked_clients

        # ----- Creating Layout ----- #
        self.endgame_tab_layout = QVBoxLayout()
        self.setLayout(self.endgame_tab_layout)
        # --------------------------- #

        # ----- Creating General Group ----- #
        self.general_group = QGroupBox("General")
        self.general_group_layout = QVBoxLayout()

        self.binding_buttons_row = QHBoxLayout()
        self.pagoda_buttons_row = QHBoxLayout()
        # ---------------------------------- #

        # ----- Creating Urnings Group ----- #
        self.urnings_group = QGroupBox("Urnings")
        self.urnings_group_layout = QHBoxLayout()
        # ---------------------------------- #

        # ----- Creating Time Torch Group ----- #
        self.time_torch_group = QGroupBox("Time Torch")
        self.time_torch_group_layout = QHBoxLayout()
        # ------------------------------------- #

        # ----- Binding Buttons Button ----- #
        binding_buttons_button = QPushButton("Binding Buttons")

        binding_buttons_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        binding_buttons_button.setMaximumHeight(50)
        binding_buttons_button.setMinimumHeight(50)

        binding_buttons_button.clicked.connect(
            lambda: asyncio.create_task(self.binding_buttons())
        )

        self.binding_buttons_row.addWidget(binding_buttons_button)
        # ---------------------------------- #

        # ----- North Pagoda Button ----- #
        north_pagoda_teleport_button = QPushButton("North Pagoda")

        north_pagoda_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        north_pagoda_teleport_button.setMaximumHeight(70)
        north_pagoda_teleport_button.setMinimumHeight(70)

        north_pagoda_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.north_pagoda_teleport())
        )

        self.pagoda_buttons_row.addWidget(north_pagoda_teleport_button)
        # ------------------------------- #

        # ----- East Pagoda Button ----- #
        east_pagoda_teleport_button = QPushButton("East Pagoda")

        east_pagoda_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        east_pagoda_teleport_button.setMaximumHeight(70)
        east_pagoda_teleport_button.setMinimumHeight(70)

        east_pagoda_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.east_pagoda_teleport())
        )

        self.pagoda_buttons_row.addWidget(east_pagoda_teleport_button)
        # ------------------------------ #

        # ----- South Pagoda Button ----- #
        south_pagoda_teleport_button = QPushButton("South Pagoda")

        south_pagoda_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        south_pagoda_teleport_button.setMaximumHeight(70)
        south_pagoda_teleport_button.setMinimumHeight(70)

        south_pagoda_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.south_pagoda_teleport())
        )

        self.pagoda_buttons_row.addWidget(south_pagoda_teleport_button)
        # ------------------------------- #

        # ----- West Pagoda Button ----- #
        west_pagoda_teleport_button = QPushButton("West Pagoda")

        west_pagoda_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        west_pagoda_teleport_button.setMaximumHeight(70)
        west_pagoda_teleport_button.setMinimumHeight(70)

        west_pagoda_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.west_pagoda_teleport())
        )

        self.pagoda_buttons_row.addWidget(west_pagoda_teleport_button)
        # ------------------------------ #

        self.general_group_layout.addLayout(self.binding_buttons_row)
        self.general_group_layout.addLayout(self.pagoda_buttons_row)

        # ----- Elemental Urning Button ----- #
        elemental_urning_teleport_button = QPushButton("Elemental Urning")

        elemental_urning_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        elemental_urning_teleport_button.setMinimumHeight(50)

        elemental_urning_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.elemental_urning_teleport())
        )

        self.urnings_group_layout.addWidget(elemental_urning_teleport_button)
        # ----------------------------------- #

        # ----- Spirit Urning Button ----- #
        spirit_urning_teleport_button = QPushButton("Spirit Urning")

        spirit_urning_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        spirit_urning_teleport_button.setMinimumHeight(50)

        spirit_urning_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.spirit_urning_teleport())
        )

        self.urnings_group_layout.addWidget(spirit_urning_teleport_button)
        # --------------------------------- #

        # ----- Time Torch Button ----- #
        time_torch_button = QPushButton("Time Torch")

        time_torch_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        time_torch_button.setMinimumHeight(75)

        time_torch_button.clicked.connect(
            lambda: asyncio.create_task(self.time_torch())
        )

        self.time_torch_group_layout.addWidget(time_torch_button)
        # ----------------------------- #

        self.general_group.setLayout(self.general_group_layout)
        self.urnings_group.setLayout(self.urnings_group_layout)
        self.time_torch_group.setLayout(self.time_torch_group_layout)

        self.endgame_tab_layout.addWidget(self.general_group)
        self.endgame_tab_layout.addWidget(self.time_torch_group)
        self.endgame_tab_layout.addWidget(self.urnings_group, 1)

    async def binding_buttons(self):
        print(f"[ENDGAME] Binding Buttons pressed.")

        print(f"not yet implemented")

    async def time_torch(self):
        print(f"[ENDGAME] Time Torch pressed.")

        await self.utils.handle_basic_teleport(-55362.516,  -3990.939,  -5028.671) # jz

    async def north_pagoda_teleport(self):
        print(f"[PAGODA] North Pagoda pressed.")

        await self.utils.handle_basic_teleport(0.0, 200.0, 204.203) # ratul

    async def east_pagoda_teleport(self):
        print(f"[PAGODA] East Pagoda pressed.")

        await self.utils.handle_basic_teleport(2300.0, -2300.0, 213.011) # ratul

    async def south_pagoda_teleport(self):
        print(f"[PAGODA] South Pagoda pressed.")

        await self.utils.handle_basic_teleport(-1350.0, -5000.0, 207.070) # ratul

    async def west_pagoda_teleport(self):
        print(f"[PAGODA] West Pagoda pressed.")

        await self.utils.handle_basic_teleport(-3600.0, -2300.0, 211.996) # ratul

    async def elemental_urning_teleport(self):
        print(f"[URNING] Elemental Urning pressed.")

        await self.utils.handle_basic_teleport(-2972.296, 90.060, 204.203) # jz

    async def spirit_urning_teleport(self):
        print(f"[URNING] Spirit Urning pressed.")

        await self.utils.handle_basic_teleport(-2798.477, 109.727, 204.203) # jz


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

        # self.utility_tab_layout.addStretch()

        self.utility_group.setLayout(self.utility_tab_layout)
        self.utility_group_layout.addWidget(self.utility_group)
        # ---------------------------------- #

        # ----- Auto Dialogue Button ----- #
        auto_dialogue_button = QPushButton("Toggle Auto Dialogue")

        auto_dialogue_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # auto_dialogue_button.setMaximumHeight(50)
        # auto_dialogue_button.setMinimumHeight(50)

        auto_dialogue_button.clicked.connect(
            lambda: asyncio.create_task(self.toggle_auto_dialogue())
        )

        self.utility_tab_layout.addWidget(auto_dialogue_button)
        # -------------------------------- #

        # ----- Speedhack Button ----- #
        speedhack_button = QPushButton("Toggle Speedhack")

        speedhack_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # speedhack_button.setMaximumHeight(50)
        # speedhack_button.setMinimumHeight(50)

        speedhack_button.clicked.connect(
            lambda: asyncio.create_task(self.toggle_speedhack())
        )

        self.utility_tab_layout.addWidget(speedhack_button)
        # ---------------------------- #

        # ----- Freecam Button ----- #
        freecam_button = QPushButton("Toggle Freecam")

        freecam_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # freecam_button.setMaximumHeight(50)
        # freecam_button.setMinimumHeight(50)

        freecam_button.clicked.connect(
            lambda: asyncio.create_task(self.toggle_freecam())
        )

        self.utility_tab_layout.addWidget(freecam_button)
        # -------------------------- #

        # ----- Freecam Teleport Button ----- #
        freecam_teleport_button = QPushButton("Freecam Teleport")

        freecam_teleport_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # freecam_teleport_button.setMaximumHeight(50)
        # freecam_teleport_button.setMinimumHeight(50)

        freecam_teleport_button.clicked.connect(
            lambda: asyncio.create_task(self.handle_freecam_teleport())
        )

        self.utility_tab_layout.addWidget(freecam_teleport_button)
        # ---------------------------------- #

        # ----- XYZ Sync Button ----- #
        xyz_sync_button = QPushButton("XYZ Sync")

        xyz_sync_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # xyz_sync_button.setMaximumHeight(50)
        # xyz_sync_button.setMinimumHeight(50)

        xyz_sync_button.clicked.connect(
            lambda: asyncio.create_task(self.handle_xyz_sync())
        )

        self.utility_tab_layout.addWidget(xyz_sync_button)
        # --------------------------- #

        # ----- Copy Position Button ----- #
        copy_position_button = QPushButton("Copy Position")

        copy_position_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # copy_position_button.setMaximumHeight(50)
        # copy_position_button.setMinimumHeight(50)

        copy_position_button.clicked.connect(
            lambda: asyncio.create_task(self.handle_copy_position())
        )

        self.utility_tab_layout.addWidget(copy_position_button)
        # ------------------------------- #

    async def toggle_auto_dialogue(self):
        print("[UTILITY] Auto Dialogue pressed.")

        if not self.auto_dialogue_tasks:
            for client in self.hooked_clients:
                self.auto_dialogue_tasks[client] = asyncio.create_task(
                    self.utils.handle_auto_dialogue(client)
                )
            return

        if self.auto_dialogue_tasks:
            for client, auto_dialogue_task in self.auto_dialogue_tasks.items():
                auto_dialogue_task.cancel()
            self.auto_dialogue_tasks = {}

    async def toggle_speedhack(self):
        print("[UTILITY] Speedhack pressed.")

        if not self.speedhack_tasks:
            for client in self.hooked_clients:
                self.speedhack_tasks[client] = asyncio.create_task(
                    self.utils.handle_speedhack(client)
                )
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
            print(
                f"[TOGGLE] Freecam cancelled."
            )  # i dont like this here but i was forced to

    async def handle_freecam_teleport(self):
        print("[UTILITY] Freecam Teleport pressed.")

        if not self.freecam_task:
            print(f"[UTILITY] Freecam is not active.")

        if self.freecam_task:
            self.freecam_task.cancel()

            camera_pos = await self.freecam_task

            self.freecam_task = None

            self.freecam_teleport_task = asyncio.create_task(
                self.utils.freecam_teleport(camera_pos)
            )

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
        # ---------------------------------- #

        # ----- Creating Preset Themes Group ----- #
        self.preset_themes_group = QGroupBox("Preset Themes")
        self.preset_themes_group_layout = QVBoxLayout()
        # ---------------------------------- #

        # ----- Default Theme Button ----- #
        default_theme_button_button = QPushButton("Default Theme")

        default_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # default_theme_button_button.setMaximumHeight(50)
        # default_theme_button_button.setMinimumHeight(50)

        default_theme_button_button.clicked.connect(self.enable_default_theme)

        self.main_themes_group_layout.addWidget(default_theme_button_button)
        # -------------------------------- #

        # ----- Raid Theme Button ----- #
        raid_theme_button_button = QPushButton("Raid Theme")

        raid_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # raid_theme_button_button.setMaximumHeight(50)
        # raid_theme_button_button.setMinimumHeight(50)

        raid_theme_button_button.clicked.connect(self.enable_raid_theme)

        self.main_themes_group_layout.addWidget(raid_theme_button_button)
        # -------------------------------- #

        # ----- Custom Theme Button ----- #
        custom_theme_button_button = QPushButton("Custom Theme")

        custom_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # custom_theme_button_button.setMaximumHeight(50)
        # custom_theme_button_button.setMinimumHeight(50)

        custom_theme_button_button.clicked.connect(self.enable_custom_theme)

        self.main_themes_group_layout.addWidget(custom_theme_button_button)
        # -------------------------------- #

        # ----- Night Theme Button ----- #
        night_theme_button_button = QPushButton("Night Theme")

        night_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # night_theme_button_button.setMaximumHeight(50)
        # night_theme_button_button.setMinimumHeight(50)

        night_theme_button_button.clicked.connect(self.enable_night_theme)

        self.preset_themes_group_layout.addWidget(night_theme_button_button)
        # -------------------------------- #

        # ----- Celestia Theme Button ----- #
        celestia_theme_button_button = QPushButton("Celestia Theme")

        celestia_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # celestia_theme_button_button.setMaximumHeight(50)
        # celestia_theme_button_button.setMinimumHeight(50)

        celestia_theme_button_button.clicked.connect(self.enable_celestia_theme)

        self.preset_themes_group_layout.addWidget(celestia_theme_button_button)
        # -------------------------------- #

        # ----- Mooshu Theme Button ----- #
        mooshu_theme_button_button = QPushButton("Mooshu Theme")

        mooshu_theme_button_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # mooshu_theme_button_button.setMaximumHeight(50)
        # mooshu_theme_button_button.setMinimumHeight(50)

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

    def enable_raid_theme(self):
        print(f"[THEMES] Raid theme enabled.")

        self.window().setStyleSheet(self.themes.raid)

    def enable_custom_theme(self):
        themes_directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "themes"
        )

        def handle_select(theme_path):
            try:
                with open(theme_path, encoding="utf-8") as theme_file:
                    theme = json.load(theme_file)

                if not isinstance(theme, dict) or not all(
                    isinstance(value, str) for value in theme.values()
                ):

                    raise ValueError("Theme settings must be an object of strings.")

                stylesheet = self.themes.build_stylesheet(theme)

            except (OSError, ValueError, KeyError) as error:
                QMessageBox.warning(
                    self.theme_dialog, "Unable to Load Theme", str(error)
                )
                return

            self.window().setStyleSheet(stylesheet)
            self.theme_dialog.close()
            print(f"[THEMES] {os.path.basename(theme_path)} theme enabled.")

        self.theme_dialog = ThemeDialog(
            themes_directory, on_select=handle_select, parent=self.window()
        )
        self.theme_dialog.show()

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
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self.always_on_top_config
        )

        self.enable_clients_tab = self.utils.read_config()["enable_clients_tab"]

        self.use_raid_theme = self.utils.read_config()["use_raid_theme"]

        if self.use_raid_theme:
            self.window().setStyleSheet(self.themes.raid)

        self.setWindowTitle("Blighted Veil Cheat Tool - Lxghtend")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.setTabPosition(
            QTabWidget.TabPosition.North
        )  # Changes tab position, North: Top, South: Bottom, West: Left, East: Right

        self.hooks_tab = HooksTab(self.utils, self.hooked_clients)
        if self.enable_clients_tab:
            self.clients_tab = ClientsTab(self.utils, self.hooked_clients)
        self.keys_tab = KeysTab(self.utils, self.hooked_clients)
        self.dryad_tab = DryadTab(self.utils, self.hooked_clients)
        self.earlygame_tab = EarlygameTab(self.utils, self.hooked_clients)
        self.endgame_tab = EndgameTab(self.utils, self.hooked_clients)
        self.utility_tab = UtilityTab(self.utils, self.hooked_clients)
        self.themes_tab = ThemesTab(self.themes)

        tabs.addTab(self.hooks_tab, "Hooks")
        if self.enable_clients_tab:
            tabs.addTab(self.clients_tab, "Clients")
        tabs.addTab(self.keys_tab, "Keys")
        tabs.addTab(self.dryad_tab, "Dryads")
        tabs.addTab(self.earlygame_tab, "Earlygame")
        tabs.addTab(self.endgame_tab, "Endgame")
        tabs.addTab(self.utility_tab, "Utility")
        tabs.addTab(self.themes_tab, "Themes")

        layout.addWidget(tabs)

        # Creating footer

        footers_layout = QHBoxLayout()

        left_layout = QHBoxLayout()
        left_layout.setSpacing(0)

        donation_link_label = QLabel(
            '<a href="https://www.buymeacoffee.com/lxghtend">Donate, </a>',
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        discord_label = QLabel(
            '<a href="https://discord.gg/2xBeynxstw">Discord</a>',
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        credit_label = QLabel(
            'Made by Lxghtend (<a href="https://github.com/Lxghtend">https://github.com/Lxghtend</a>)',
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        donation_link_label.setOpenExternalLinks(True)
        discord_label.setOpenExternalLinks(True)
        credit_label.setOpenExternalLinks(True)

        left_layout.addWidget(donation_link_label)
        left_layout.addWidget(discord_label)

        footers_layout.addLayout(left_layout)
        footers_layout.addStretch()

        footers_layout.addWidget(credit_label)

        layout.addLayout(footers_layout)

        self.start_keybinds()

    def start_keybinds(self):
        def run_threadsafe(coroutine):
            asyncio.run_coroutine_threadsafe(coroutine, self.loop)

        keybinds = {
            self.utils.read_config()[
                "handle_xyz_sync"
            ]: self.utility_tab.handle_xyz_sync,
            self.utils.read_config()[
                "toggle_auto_dialogue"
            ]: self.utility_tab.toggle_auto_dialogue,
            self.utils.read_config()[
                "toggle_speedhack"
            ]: self.utility_tab.toggle_speedhack,
            self.utils.read_config()["toggle_freecam"]: self.utility_tab.toggle_freecam,
            self.utils.read_config()[
                "handle_freecam_teleport"
            ]: self.utility_tab.handle_freecam_teleport,
        }

        for keybind, function in keybinds.items():
            keyboard.add_hotkey(keybind, lambda func=function: run_threadsafe(func()))


class ThemeDialog(QDialog):
    def __init__(self, themes_directory: str, on_select, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Custom Themes")
        self.setMinimumWidth(240)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        try:
            theme_files = sorted(
                entry.name for entry in os.scandir(themes_directory)
                if entry.is_file() and entry.name.lower().endswith(".json")
            )

        except OSError:
            theme_files = []

        for theme_file in theme_files:
            theme_path = os.path.join(themes_directory, theme_file)
            theme_button = QPushButton(theme_file)
            theme_button.setMinimumHeight(40)

            theme_button.clicked.connect(
                lambda checked=False, target=theme_path: on_select(target)
            )

            layout.addWidget(theme_button)

        if not theme_files:
            layout.addWidget(QLabel("No JSON theme files found."))


class WispDialog(QDialog):
    def __init__(self, wisps: list, on_select, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Wisps")
        self.setMinimumWidth(240)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        for wisp in wisps:
            if isinstance(wisp, (list, tuple)) and len(wisp) >= 3:
                name_str, xyz, client_obj = wisp[0], wisp[1], wisp[2]
                button_text = f"{name_str} ({xyz})"
                target = client_obj
            else:
                button_text = str(wisp)
                target = wisp

            wisp_button = QPushButton(button_text)
            wisp_button.setMinimumHeight(40)
            wisp_button.clicked.connect(
                lambda checked=False, target=target: on_select(target)
            )
            layout.addWidget(wisp_button)

        self.setLayout(layout)


class DisclaimerDialog(QDialog):
    def __init__(self, parent: MainWindow = None):
        super().__init__(parent)

        self.setWindowTitle("Disclaimer")
        self.setFixedSize(240, 150)
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


class UpdaterDialog(QDialog):
    def __init__(self, parent: MainWindow = None):
        super().__init__(parent)

        self.setWindowTitle("Updater")
        self.setFixedSize(210, 150)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        label = QLabel("An update was found...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        update_button = QPushButton("Update")
        update_button.clicked.connect(
            lambda: trigger_update(tool_dir=os.path.dirname(os.path.abspath(__file__)))
        )

        ok_button = QPushButton("Ignore")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addWidget(update_button)
        layout.addWidget(ok_button)

        self.setLayout(layout)


def main():
    outdated, local, remote = check_for_update()

    app = QApplication(sys.argv)

    send_ping()

    appid = "lxghtend.blightedveil.tool.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    app.setWindowIcon(QIcon("icon.ico"))

    app.setStyle("Fusion")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(loop)
    window.show()

    disclaimer = DisclaimerDialog(window)

    if outdated:
        updater = UpdaterDialog(window)
        updater.finished.connect(
            disclaimer.show
        )  # shows disclaimer after updater closed
        updater.show()

    else:
        disclaimer.show()

    with loop:
        loop.run_forever()

    # sys.exit(app.exec())


if __name__ == "__main__":
    main()
