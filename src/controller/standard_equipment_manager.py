"""
Controller class responsible for managing standard equipment units.

Design notes:
  - Standard equipment is built into rooms (e.g. whiteboard, projector, chairs).
    It is NOT portable or bookable — it is permanently installed in a specific room.
  - Each CSV row represents ONE physical unit belonging to ONE room.
  - The 'standard_equipment' free-text column has been removed from rooms.csv.
    A room's equipment is now derived by querying get_equipment_by_room(room_id).
  - Status values: 'available', 'under_maintenance', 'damaged'.
    Individual units can be flagged without affecting room-level availability.
  - RoomManager delegates equipment keyword filtering to
    search_rooms_by_keyword(), which returns rooms that have at least one
    matching unit. This fixes Bug 5 (equipment_keyword TypeError).
"""

import csv
import os

from entity.standard_equipment import StandardEquipment


class StandardEquipmentManager:
    """Manages standard equipment physical units: CRUD, status updates,
    room association, and keyword-based room filtering."""

    EQUIPMENT_FILE = os.path.join(os.path.dirname(__file__),
                                   "../data/standard_equipment.csv")

    HEADERS = ["equipment_id", "room_id", "name", "status"]

    def __init__(self):
        self.__equipment: list[StandardEquipment] = []
        self.__load_equipment()

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def __load_equipment(self):
        """Load all standard equipment units from CSV into memory."""
        self.__equipment = []
        path = os.path.abspath(self.EQUIPMENT_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_room_id = row["room_id"].strip()
                room_id = raw_room_id if raw_room_id else None
                item = StandardEquipment(
                    equipment_id=row["equipment_id"],
                    room_id=room_id,
                    name=row["name"],
                    status=row.get("status", StandardEquipment.STATUS_AVAILABLE)
                )
                self.__equipment.append(item)

    def __save_equipment(self):
        """Persist all standard equipment units back to CSV."""
        path = os.path.abspath(self.EQUIPMENT_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for item in self.__equipment:
                writer.writerow(item.to_csv_row())

    def __generate_equipment_id(self) -> str:
        """Generate the next sequential unique equipment ID (e.g. SE001)."""
        existing = {e.get_equipment_id() for e in self.__equipment}
        i = 1
        while True:
            eid = f"SE{i:03d}"
            if eid not in existing:
                return eid
            i += 1

    # ------------------------------------------------------------------ #
    #  Public methods — Read
    # ------------------------------------------------------------------ #

    def get_all_equipment(self) -> list[StandardEquipment]:
        """Return all standard equipment units in the system."""
        return list(self.__equipment)

    def find_by_id(self, equipment_id: str) -> StandardEquipment | None:
        """Find a unit by its ID (case-insensitive)."""
        for e in self.__equipment:
            if e.get_equipment_id().upper() == equipment_id.upper():
                return e
        return None

    def get_equipment_by_room(self, room_id: str) -> list[StandardEquipment]:
        """
        Return all physical units installed in a given room.

        Used to display a room's standard equipment to the user,
        replacing the old free-text standard_equipment field on Room.

        Args:
            room_id (str): The room ID to look up, e.g. 'R001'.

        Returns:
            list[StandardEquipment]: All units belonging to that room.
        """
        return [e for e in self.__equipment
                if e.get_room_id() is not None
                and e.get_room_id().upper() == room_id.upper()]

    def get_available_equipment_by_room(self, room_id: str) -> list[StandardEquipment]:
        """
        Return only available (not damaged or under maintenance) units
        installed in a given room.

        Args:
            room_id (str): The room ID to look up.

        Returns:
            list[StandardEquipment]: Available units in that room.
        """
        return [e for e in self.get_equipment_by_room(room_id)
                if e.is_available()]

    def search_rooms_by_keyword(self, keyword: str,
                                rooms: list) -> list:
        """
        Filter a list of rooms to those that have at least one standard
        equipment unit whose name matches the keyword (case-insensitive).

        This is the method RoomManager.view_room_by_filtering() calls
        when the equipment_keyword filter is provided, fixing Bug 5.

        Args:
            keyword (str): The search term entered by the user,
                           e.g. 'projector', 'whiteboard', 'chair'.
            rooms (list[Room]): The candidate room list to filter.

        Returns:
            list[Room]: Rooms that have at least one matching unit.

        Example:
            keyword = 'projector'
            → only R005 and R006 are returned (large rooms with projectors)
        """
        kw = keyword.strip().lower()
        if not kw:
            return list(rooms)

        matching_room_ids = {
            e.get_room_id()
            for e in self.__equipment
            if e.get_room_id() is not None
            and kw in e.get_name().lower()
        }
        return [r for r in rooms if r.get_room_id() in matching_room_ids]

    def get_equipment_summary_by_room(self, room_id: str) -> str:
        """
        Return a human-readable summary of all equipment in a room,
        grouping units of the same name and showing count.

        Replaces the old Room.get_standard_equipment() free-text field
        for display purposes.

        Example output: "1 x Meeting Table, 10 x Chair, 1 x Projector"

        Args:
            room_id (str): The room ID to summarise.

        Returns:
            str: Formatted equipment summary, or 'None' if room has no units.
        """
        units = self.get_equipment_by_room(room_id)
        if not units:
            return "None"

        counts: dict[str, int] = {}
        for unit in units:
            counts[unit.get_name()] = counts.get(unit.get_name(), 0) + 1

        return ", ".join(
            f"{count} x {name}" for name, count in counts.items()
        )

    # ------------------------------------------------------------------ #
    #  Public methods — Create
    # ------------------------------------------------------------------ #

    def add_equipment(self, room_id: str | None, name: str,
                      status: str = StandardEquipment.STATUS_AVAILABLE
                      ) -> tuple[bool, str]:
        """
        Register a new physical standard equipment unit.
        Returns (success, equipment_id or error message).

        Args:
            room_id (str | None): The room this unit belongs to, or None to add to inventory.
            name    (str): Equipment type name, e.g. 'Chair'.
            status  (str): Initial status. Defaults to 'available'.
        """
        if not name.strip():
            return False, "Equipment name cannot be empty."
        if status.strip().lower() not in StandardEquipment.VALID_STATUSES:
            return False, (f"Invalid status '{status}'. "
                           f"Must be one of: "
                           f"{', '.join(StandardEquipment.VALID_STATUSES)}.")

        equipment_id = self.__generate_equipment_id()
        new_item = StandardEquipment(
            equipment_id=equipment_id,
            room_id=room_id.strip().upper() if room_id else None,
            name=name.strip(),
            status=status.strip().lower()
        )
        self.__equipment.append(new_item)
        self.__save_equipment()
        return True, equipment_id

    def add_equipment_bulk(self, room_id: str,
                           items: list[tuple[str, int]]
                           ) -> tuple[bool, str]:
        """
        Register multiple units of the same or different types for a room
        in one call. Useful when setting up a new room.

        Args:
            room_id (str): The room these units belong to.
            items (list[tuple[str, int]]): List of (name, quantity) pairs.
                  e.g. [("Chair", 6), ("Big Table", 1), ("Whiteboard", 1)]

        Returns:
            (True, "X units added to room RY") on success.
            (False, error message) if any item fails validation.
        """
        if not room_id.strip():
            return False, "Room ID cannot be empty."
        if not items:
            return False, "Items list cannot be empty."

        count = 0
        for name, quantity in items:
            if not name.strip():
                return False, "Equipment name cannot be empty."
            if not isinstance(quantity, int) or quantity < 1:
                return False, f"Quantity for '{name}' must be a positive integer."
            for _ in range(quantity):
                equipment_id = self.__generate_equipment_id()
                new_item = StandardEquipment(
                    equipment_id=equipment_id,
                    room_id=room_id.strip().upper(),
                    name=name.strip()
                )
                self.__equipment.append(new_item)
                count += 1

        self.__save_equipment()
        return True, f"{count} unit(s) added to room {room_id.strip().upper()}."

    # ------------------------------------------------------------------ #
    #  Public methods — Update
    # ------------------------------------------------------------------ #

    def update_status(self, equipment_id: str,
                      status: str) -> tuple[bool, str]:
        """
        Update the status of a single equipment unit.
        Returns (success, message).

        Args:
            equipment_id (str): The unit to update.
            status       (str): New status value.
        """
        item = self.find_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID '{equipment_id}' not found."

        try:
            item.set_status(status)
        except ValueError as e:
            return False, str(e)

        self.__save_equipment()
        return True, (f"Equipment '{equipment_id}' status updated "
                      f"to '{status}'.")

    def update_name(self, equipment_id: str,
                    name: str) -> tuple[bool, str]:
        """
        Update the name of a single equipment unit.

        If the unit is currently assigned to a room, the new name must comply
        with that room's equipment spec — both the allowed-names list and the
        per-name quantity cap. Units in inventory can be renamed freely.

        Returns (success, message).
        """
        from entity.room import Room

        item = self.find_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID '{equipment_id}' not found."
        if not name.strip():
            return False, "Equipment name cannot be empty."

        new_name = name.strip()
        old_name = item.get_name()

        # No-op rename: short-circuit silently as success.
        if new_name == old_name:
            return True, f"Equipment '{equipment_id}' name is unchanged."

        # If the unit is in inventory, no spec validation needed.
        if item.is_in_inventory():
            item.set_name(new_name)
            self.__save_equipment()
            return True, f"Equipment '{equipment_id}' name updated to '{new_name}'."

        # Unit is assigned to a room — validate against the room's spec.
        room_id = item.get_room_id()
        # Need to find the room's type. Look up via any other unit in the room
        # or rely on RoomManager. Cleanest approach: derive from a sibling unit
        # is fragile — instead, validate against ALL room-type specs that include
        # the room's current equipment names.
        #
        # Better: look the room up directly. But this controller doesn't hold
        # a RoomManager reference. We can avoid that by inferring the room_type
        # from the existing units' names matching exactly one of the specs.
        # Simpler and more robust: import RoomManager lazily.
        from controller.room_manager import RoomManager
        room = RoomManager().find_room_by_id(room_id)
        if room is None:
            # Room no longer exists — treat unit as inventory-bound for safety.
            item.set_name(new_name)
            self.__save_equipment()
            return True, f"Equipment '{equipment_id}' name updated to '{new_name}'."

        room_type = room.get_room_type()
        spec = Room.STANDARD_EQUIPMENT.get(room_type)
        if spec is None:
            return False, f"Unknown room type '{room_type}' for room {room_id}."

        # 1. New name must be in the spec for the room's type.
        if new_name not in spec:
            allowed = ", ".join(spec.keys())
            return False, (f"'{new_name}' is not allowed in a {room_type} room. "
                           f"Allowed types: {allowed}.")

        # 2. Quantity cap for the NEW name must not be exceeded.
        #    Count existing units of new_name in this room, excluding this unit.
        current_count = sum(
            1 for e in self.get_equipment_by_room(room_id)
            if e.get_name() == new_name and e.get_equipment_id() != equipment_id
        )
        max_allowed = spec[new_name]
        if current_count >= max_allowed:
            return False, (f"Cannot rename: room {room_id} already has "
                           f"{current_count} x '{new_name}' "
                           f"(max {max_allowed} for {room_type} room).")

        item.set_name(new_name)
        self.__save_equipment()
        return True, f"Equipment '{equipment_id}' name updated to '{new_name}'."

    def get_inventory(self) -> list[StandardEquipment]:
        """Return all units currently held in inventory (not assigned to any room)."""
        return [e for e in self.__equipment if e.is_in_inventory()]

    def assign_to_room(self, equipment_id: str,
                       room_id: str,
                       room_type: str) -> tuple[bool, str]:
        """
        Assign an inventory unit to a room.
        Validates that the equipment name is permitted for the room type and
        that the current count of that name has not already reached the spec maximum.
        Returns (success, message).

        Args:
            equipment_id (str): The unit to assign.
            room_id      (str): The room to assign it to.
            room_type    (str): The room type (e.g. 'small', 'medium', 'large'),
                                used to look up the allowed spec.
        """
        from entity.room import Room

        item = self.find_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID '{equipment_id}' not found."
        if not item.is_in_inventory():
            return False, (f"Equipment '{equipment_id}' is already assigned "
                           f"to room {item.get_room_id()}.")

        spec = Room.STANDARD_EQUIPMENT.get(room_type.lower())
        if spec is None:
            return False, f"Unknown room type '{room_type}'."

        # Validate equipment name is allowed for this room type
        if item.get_name() not in spec:
            allowed = ", ".join(spec.keys())
            return False, (f"'{item.get_name()}' is not allowed in a "
                           f"{room_type} room. Allowed types: {allowed}.")

        # Validate quantity cap
        current_count = sum(
            1 for e in self.get_equipment_by_room(room_id)
            if e.get_name() == item.get_name()
        )
        max_allowed = spec[item.get_name()]
        if current_count >= max_allowed:
            return False, (f"Cannot assign: room {room_id} already has "
                           f"{current_count} x '{item.get_name()}' "
                           f"(max {max_allowed} for {room_type} room).")

        item.set_room_id(room_id.strip().upper())
        self.__save_equipment()
        return True, (f"Equipment '{equipment_id}' ({item.get_name()}) "
                      f"assigned to room {room_id.strip().upper()}.")

    def unassign_from_room(self, equipment_id: str) -> tuple[bool, str]:
        """
        Move a unit from its current room into inventory.
        Returns (success, message).

        Args:
            equipment_id (str): The unit to unassign.
        """
        item = self.find_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID '{equipment_id}' not found."
        if item.is_in_inventory():
            return False, f"Equipment '{equipment_id}' is already in inventory."
        old_room = item.get_room_id()
        item.set_room_id(None)
        self.__save_equipment()
        return True, (f"Equipment '{equipment_id}' moved from room "
                      f"{old_room} to inventory.")

    def unassign_all_from_room(self, room_id: str) -> tuple[bool, str]:
        """
        Move all units belonging to a room into inventory.
        Used when a room is deleted — equipment is preserved in inventory
        rather than permanently removed.
        Returns (success, message).
        """
        units = self.get_equipment_by_room(room_id)
        if not units:
            return False, f"No standard equipment found for room '{room_id}'."
        for unit in units:
            unit.set_room_id(None)
        self.__save_equipment()
        return True, f"{len(units)} unit(s) moved to inventory from room {room_id}."

    # ------------------------------------------------------------------ #
    #  Public methods — Delete
    # ------------------------------------------------------------------ #

    def delete_equipment(self, equipment_id: str) -> tuple[bool, str]:
        """
        Permanently remove a single standard equipment unit from the system.
        Returns (success, message).
        """
        item = self.find_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID '{equipment_id}' not found."

        self.__equipment.remove(item)
        self.__save_equipment()
        location = f"room {item.get_room_id()}" if not item.is_in_inventory() else "inventory"
        return True, (f"Standard equipment '{item.get_name()}' "
                      f"({equipment_id}) permanently removed from {location}.")

    def delete_equipment_by_room(self, room_id: str) -> tuple[bool, str]:
        """
        Permanently remove all standard equipment units belonging to a room.
        NOTE: prefer unassign_all_from_room() to preserve equipment in inventory.
        Returns (success, message).
        """
        units = self.get_equipment_by_room(room_id)
        if not units:
            return False, f"No standard equipment found for room '{room_id}'."

        for unit in units:
            self.__equipment.remove(unit)

        self.__save_equipment()
        return True, (f"{len(units)} unit(s) permanently removed for room {room_id}.")