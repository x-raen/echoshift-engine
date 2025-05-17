# AGEE: Gadget Database - x-raen's Repository of Exploitable Code Snippets

"""
Within the grand design of EchoShift, x-raen meticulously curates this Gadget Database (GadgetDB)
for the Advanced Gadget Equivalence Engine (AGEE). This is not merely a collection;
it is a living arsenal of code snippets, each analyzed, indexed, and ready to be
deployed in the art of ROP/JOP chain transformation.
"""

from typing import List, Dict, Any, Optional, Set
import json
import os

# Assuming AGEEGadget and other necessary structures are defined in agee_data_structures
# For standalone development or testing, we might need to redefine or import them.
# from .agee_data_structures import AGEEGadget, SDUOperand # (If SDUOperand is used for gadget properties)

# Placeholder for AGEEGadget if not directly importable during isolated development
class AGEEGadget_Placeholder:
    def __init__(self, gadget_string: str, address: Optional[int] = None, item_id: Optional[str] = None):
        self.item_id = item_id if item_id else f"gadget_{hash(gadget_string)}_{address if address else ''}"
        self.gadget_string = gadget_string
        self.address = address
        self.instructions: List[Dict[str, Any]] = []
        self.properties: Dict[str, Any] = {"raw_string": gadget_string}
        if address is not None:
            self.properties["address"] = address
        self.equivalence_signatures: Set[str] = set()

    def add_property(self, key: str, value: Any):
        self.properties[key] = value

    def add_signature(self, signature: str):
        self.equivalence_signatures.add(signature)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "gadget_string": self.gadget_string,
            "address": self.address,
            "instructions": self.instructions,
            "properties": self.properties,
            "equivalence_signatures": list(self.equivalence_signatures)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AGEEGadget_Placeholder":
        gadget = cls(data["gadget_string"], data.get("address"), item_id=data.get("item_id"))
        gadget.instructions = data.get("instructions", [])
        gadget.properties = data.get("properties", {})
        gadget.equivalence_signatures = set(data.get("equivalence_signatures", []))
        return gadget

# Use the actual AGEEGadget if available, otherwise the placeholder
try:
    from .agee_data_structures import AGEEGadget
except ImportError:
    AGEEGadget = AGEEGadget_Placeholder # type: ignore

class GadgetDB_xraen:
    """x-raen's Gadget Database: The heart of AGEE's knowledge about available gadgets."""

    def __init__(self, db_path: Optional[str] = None):
        """Initializes the Gadget Database.

        Args:
            db_path (Optional[str]): Path to a file to load/save the database. 
                                     If None, operates in-memory.
        """
        self.gadgets: Dict[str, AGEEGadget] = {} # item_id -> AGEEGadget object
        self.db_path = db_path
        self._index: Dict[str, Set[str]] = {} # For simple indexing, e.g., "mnemonic:mov" -> {gadget_id1, gadget_id2}
        
        if self.db_path and os.path.exists(self.db_path):
            self.load_from_file(self.db_path)
        
        print(f"[x-raen_GadgetDB] Gadget Database initialized. Loaded {len(self.gadgets)} gadgets.")

    def add_gadget(self, gadget: AGEEGadget, re_index: bool = True) -> bool:
        """Adds a new gadget to the database, a new instrument in x-raen's orchestra.

        Args:
            gadget (AGEEGadget): The gadget object to add.
            re_index (bool): Whether to update the index after adding.

        Returns:
            bool: True if added successfully, False if gadget_id already exists.
        """
        if gadget.item_id in self.gadgets:
            print(f"[x-raen_GadgetDB_Warning] Gadget with ID {gadget.item_id} already exists. Not adding.")
            return False
        self.gadgets[gadget.item_id] = gadget
        if re_index:
            self._update_index_for_gadget(gadget)
        print(f"[x-raen_GadgetDB] Gadget added: {gadget.item_id}")
        return True

    def get_gadget(self, gadget_id: str) -> Optional[AGEEGadget]:
        """Retrieves a gadget by its ID, a specific note from x-raen's score.
        """
        return self.gadgets.get(gadget_id)

    def remove_gadget(self, gadget_id: str) -> bool:
        """Removes a gadget from the database.
        """
        if gadget_id in self.gadgets:
            gadget_to_remove = self.gadgets.pop(gadget_id)
            self._remove_from_index(gadget_to_remove) # Clean up index
            print(f"[x-raen_GadgetDB] Gadget removed: {gadget_id}")
            return True
        print(f"[x-raen_GadgetDB_Warning] Gadget with ID {gadget_id} not found for removal.")
        return False

    def _update_index_for_gadget(self, gadget: AGEEGadget):
        """x-raen meticulously indexes each gadget for swift retrieval.
        This is a simplified index based on mnemonics and properties.
        """
        # Index by mnemonics
        for instr_data in gadget.instructions:
            mnemonic = instr_data.get("mnemonic", "").lower()
            if mnemonic:
                idx_key = f"mnemonic:{mnemonic}"
                if idx_key not in self._index:
                    self._index[idx_key] = set()
                self._index[idx_key].add(gadget.item_id)
        
        # Index by other significant properties (example)
        if "sdu_type" in gadget.properties: # If it was derived from an SDU segment
            sdu_type_val = str(gadget.properties["sdu_type"])
            idx_key = f"sdu_type:{sdu_type_val}"
            if idx_key not in self._index:
                self._index[idx_key] = set()
            self._index[idx_key].add(gadget.item_id)
        
        # Index by equivalence signatures
        for sig in gadget.equivalence_signatures:
            idx_key = f"signature:{sig}"
            if idx_key not in self._index:
                self._index[idx_key] = set()
            self._index[idx_key].add(gadget.item_id)

    def _remove_from_index(self, gadget: AGEEGadget):
        """Removes a gadget's entries from the index."""
        keys_to_check = []
        for instr_data in gadget.instructions:
            mnemonic = instr_data.get("mnemonic", "").lower()
            if mnemonic: keys_to_check.append(f"mnemonic:{mnemonic}")
        if "sdu_type" in gadget.properties:
            keys_to_check.append(f"sdu_type:{str(gadget.properties['sdu_type'])}")
        for sig in gadget.equivalence_signatures:
            keys_to_check.append(f"signature:{sig}")
        
        for key in keys_to_check:
            if key in self._index and gadget.item_id in self._index[key]:
                self._index[key].remove(gadget.item_id)
                if not self._index[key]: # Remove key if set is empty
                    del self._index[key]

    def build_index(self):
        """Rebuilds the entire index from scratch. x-raen ensures order and precision."""
        self._index.clear()
        for gadget_id, gadget in self.gadgets.items():
            self._update_index_for_gadget(gadget)
        print(f"[x-raen_GadgetDB] Index rebuilt. {len(self._index)} index keys.")

    def search_gadgets(self, query_properties: Dict[str, Any], match_all: bool = True) -> List[AGEEGadget]:
        """Searches for gadgets based on a dictionary of properties.
        x-raen's query language to find the perfect code snippet.

        Args:
            query_properties: Dict where keys are property names (e.g., "mnemonic", "sdu_type", "signature")
                              and values are the desired property values.
                              Example: {"mnemonic:pop": True, "sdu_type:LOAD_REGISTER": True}
                                       {"signature:AFFECTS_RAX": True}
            match_all: If True, gadgets must match all properties. If False, any match is sufficient.

        Returns:
            List of matching AGEEGadget objects.
        """
        candidate_sets: List[Set[str]] = []
        for key_prop, value_prop in query_properties.items():
            # Assuming query format like "mnemonic:pop" or "signature:AFFECTS_RAX"
            # For boolean properties in the query, value_prop would be True
            if value_prop is True: # Only consider properties marked as True in the query
                indexed_gadget_ids = self._index.get(key_prop, set())
                candidate_sets.append(indexed_gadget_ids)
            # Add more complex query logic if needed (e.g., property value matching)

        if not candidate_sets:
            return []

        if match_all:
            # Intersection of all sets
            if not candidate_sets: return []
            result_ids = candidate_sets[0].copy()
            for i in range(1, len(candidate_sets)):
                result_ids.intersection_update(candidate_sets[i])
        else:
            # Union of all sets
            result_ids = set()
            for s in candidate_sets:
                result_ids.update(s)
        
        return [self.gadgets[gid] for gid in result_ids if gid in self.gadgets]

    def save_to_file(self, file_path: Optional[str] = None):
        """Saves the gadget database to a JSON file, preserving x-raen's collection.
        """
        path_to_save = file_path if file_path else self.db_path
        if not path_to_save:
            print("[x-raen_GadgetDB_Error] No file path provided for saving.")
            return
        
        try:
            db_data = {
                "gadgets": {gid: g.to_dict() for gid, g in self.gadgets.items()}
                # Index can be rebuilt, so not saving it explicitly unless very large and static
            }
            with open(path_to_save, "w") as f:
                json.dump(db_data, f, indent=4)
            print(f"[x-raen_GadgetDB] Database saved to {path_to_save}")
        except Exception as e:
            print(f"[x-raen_GadgetDB_Error] Failed to save database: {e}")

    def load_from_file(self, file_path: str):
        """Loads the gadget database from a JSON file, restoring x-raen's knowledge.
        """
        if not os.path.exists(file_path):
            print(f"[x-raen_GadgetDB_Warning] Database file not found: {file_path}")
            return
        
        try:
            with open(file_path, "r") as f:
                db_data = json.load(f)
            
            self.gadgets.clear()
            loaded_gadgets_data = db_data.get("gadgets", {})
            for gid, g_data in loaded_gadgets_data.items():
                self.gadgets[gid] = AGEEGadget.from_dict(g_data)
            
            self.build_index() # Rebuild index after loading
            print(f"[x-raen_GadgetDB] Database loaded from {file_path}. {len(self.gadgets)} gadgets.")
            self.db_path = file_path # Update db_path if loaded from a new file
        except Exception as e:
            print(f"[x-raen_GadgetDB_Error] Failed to load database: {e}")

    def get_all_gadgets(self) -> List[AGEEGadget]:
        """Returns all gadgets currently in the database."""
        return list(self.gadgets.values())

# --- Example Usage and x-raen's Test Bench ---
if __name__ == "__main__":
    print("\n--- AGEE Gadget Database: x-raen's Arsenal of Code ---")
    
    # Initialize DB (in-memory for this test)
    gadget_db = GadgetDB_xraen(db_path="./test_gadget_db_xraen.json")
    if os.path.exists("./test_gadget_db_xraen.json"): # Clean up previous test file
        os.remove("./test_gadget_db_xraen.json")
    gadget_db = GadgetDB_xraen(db_path="./test_gadget_db_xraen.json") # Re-init to ensure clean start if file existed

    # Create some sample AGEEGadget objects (using placeholder if full SDU/AGEE not integrated)
    gadget1_str = "pop rax; ret"
    gadget1 = AGEEGadget(gadget_string=gadget1_str, address=0x401000)
    gadget1.instructions = [{"mnemonic": "pop", "operands_str": "rax"}, {"mnemonic": "ret", "operands_str": ""}]
    gadget1.add_signature("LOAD_FROM_STACK")
    gadget1.add_signature("AFFECTS_RAX")
    gadget1.add_property("sdu_type", "LOAD_REGISTER") # Example property

    gadget2_str = "mov rdi, rsi; ret"
    gadget2 = AGEEGadget(gadget_string=gadget2_str, address=0x402000)
    gadget2.instructions = [{"mnemonic": "mov", "operands_str": "rdi, rsi"}, {"mnemonic": "ret", "operands_str": ""}]
    gadget2.add_signature("REGISTER_TRANSFER")
    gadget2.add_signature("AFFECTS_RDI")

    gadget3_str = "pop rbx; pop rax; ret;" # A slightly different pop rax
    gadget3 = AGEEGadget(gadget_string=gadget3_str, address=0x403000)
    gadget3.instructions = [{"mnemonic": "pop", "operands_str": "rbx"}, {"mnemonic": "pop", "operands_str": "rax"}, {"mnemonic": "ret", "operands_str": ""}]
    gadget3.add_signature("LOAD_FROM_STACK") # Same signature as gadget1
    gadget3.add_signature("AFFECTS_RAX")
    gadget3.add_signature("AFFECTS_RBX")

    # Add to DB
    gadget_db.add_gadget(gadget1)
    gadget_db.add_gadget(gadget2)
    gadget_db.add_gadget(gadget3)

    print(f"\nTotal gadgets in DB: {len(gadget_db.get_all_gadgets())}")

    # Test Search
    print("\n--- Testing Search --- ")
    query1 = {"mnemonic:pop": True, "signature:AFFECTS_RAX": True}
    results1 = gadget_db.search_gadgets(query1)
    print(f"Search for 'pop' AND 'AFFECTS_RAX' ({len(results1)} results):")
    for g in results1: print(f"  Found: {g.gadget_string} at 0x{g.address:x if g.address else 0}")

    query2 = {"signature:LOAD_FROM_STACK": True}
    results2 = gadget_db.search_gadgets(query2, match_all=True)
    print(f"\nSearch for signature 'LOAD_FROM_STACK' ({len(results2)} results):")
    for g in results2: print(f"  Found: {g.gadget_string}")

    query3 = {"mnemonic:mov": True}
    results3 = gadget_db.search_gadgets(query3)
    print(f"\nSearch for 'mov' ({len(results3)} results):")
    for g in results3: print(f"  Found: {g.gadget_string}")
    
    # Test Save and Load
    print("\n--- Testing Save and Load --- ")
    gadget_db.save_to_file() # Saves to ./test_gadget_db_xraen.json
    
    new_db_instance = GadgetDB_xraen(db_path="./test_gadget_db_xraen.json")
    print(f"Gadgets in new loaded instance: {len(new_db_instance.get_all_gadgets())}")
    loaded_gadget1 = new_db_instance.get_gadget(gadget1.item_id)
    if loaded_gadget1:
        print(f"Successfully loaded gadget1: {loaded_gadget1.gadget_string}")
        print(f"  Signatures: {loaded_gadget1.equivalence_signatures}")
    else:
        print("Failed to load gadget1 from new instance.")

    # Clean up test file
    if os.path.exists("./test_gadget_db_xraen.json"):
        os.remove("./test_gadget_db_xraen.json")
        print("\nCleaned up test_gadget_db_xraen.json")

    print("\nx-raen's Gadget Database stands ready, a testament to structured knowledge!")


