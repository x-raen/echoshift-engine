# AGEE: Application Programming Interface (API) - x-raen's Blueprint for Creative Integration

"""
Here, within the realm of "EchoShift", x-raen builds the bridges of communication
between the Advanced Gadget Equivalence Engine (AGEE) and the rest of the system.
This API is not just a set of connection points, but an invitation for collaborative creation,
where the Semantic Deconstruction Unit (SDU), AGEE, and the Reconstruction & Patching Unit (RPU)
harmonize in a symphony of understanding and intelligent adaptation.
"""

from typing import List, Dict, Any, Optional, Tuple

# Depending on AGEE data structures and core engine (assuming availability)
from .agee_data_structures import (
    AGEEComparableItem, AGEEFunctionalSegment, AGEEGadget,
    EquivalenceCriteria, EquivalencePair, SDUFunctionalSegment, SDUSegmentType
)
from .agee_core_engine import AGEECoreEngine

class AGEE_API_Facade_By_xraen:
    """AGEE API Facade - x-raen's design for inter-unit harmony.
    This interface is the gateway through which data and commands flow,
    weaving the threads of equivalence and deep understanding.
    """

    def __init__(self, core_engine: Optional[AGEECoreEngine] = None):
        """x-raen begins by preparing the equivalence engine, the beating heart of this interface."""
        self.engine = core_engine if core_engine else AGEECoreEngine()
        print("[x-raen_AGEE_API] AGEE API awakens, ready to serve creativity!")

    def register_sdu_functional_segment(self, sdu_segment_data: Dict[str, Any]) -> Optional[AGEEFunctionalSegment]:
        """Registers a functional segment from SDU to become part of AGEE's world.
        Here, x-raen receives SDU's treasures to refine them with the touch of equivalence.

        Args:
            sdu_segment_data: A dictionary containing the SDU functional segment data.
                              Example: {
                                  "segment_type": "LOAD_REGISTER",
                                  "original_gadgets": ["pop rax", "ret"],
                                  "effects": ["RAX = [RSP]"],
                                  "symbolic_representation": {"writes": {"RAX": "mem[initial_RSP]"}}
                              }
        Returns:
            An AGEEFunctionalSegment object if registration is successful, else None.
        """
        try:
            # Convert type name to Enum member
            segment_type_str = sdu_segment_data.get("segment_type")
            if not segment_type_str or not hasattr(SDUSegmentType, segment_type_str):
                print(f"[x-raen_AGEE_API_Error] Invalid SDU segment type: {segment_type_str}")
                return None
            segment_type_enum = SDUSegmentType[segment_type_str]
            
            sdu_fs = SDUFunctionalSegment(
                segment_type=segment_type_enum,
                original_gadgets=sdu_segment_data.get("original_gadgets", []),
                effects=sdu_segment_data.get("effects", []),
                symbolic_representation=sdu_segment_data.get("symbolic_representation")
            )
            agee_fs = AGEEFunctionalSegment(sdu_fs)
            self.engine.register_item(agee_fs)
            print(f"[x-raen_AGEE_API] SDU segment registered successfully: {agee_fs.item_id}")
            return agee_fs
        except Exception as e:
            print(f"[x-raen_AGEE_API_Error] Failed to register SDU segment: {e}")
            return None

    def register_raw_gadget(self, gadget_string: str, address: Optional[int] = None) -> Optional[AGEEGadget]:
        """Registers a raw gadget (string) for analysis and comparison in AGEE.
        Even the smallest gadgets have an echo in x-raen's world.
        """
        try:
            agee_gadget = AGEEGadget(gadget_string, address)
            # An initial disassembly step could be added here if needed before full registration
            # self.engine.disassemble_and_enhance_gadget(agee_gadget) # Example
            self.engine.register_item(agee_gadget)
            print(f"[x-raen_AGEE_API] Raw gadget registered successfully: {agee_gadget.item_id}")
            return agee_gadget
        except Exception as e:
            print(f"[x-raen_AGEE_API_Error] Failed to register raw gadget: {e}")
            return None

    def find_equivalences_for_item(self, item_id: str, criteria: Optional[List[str]] = None, min_confidence: float = 0.7) -> List[EquivalencePair]:
        """Finds all items equivalent to a given item based on specified criteria.
        x-raen unleashes AGEE's power to uncover hidden connections.

        Args:
            item_id: The unique ID of the item to find equivalences for.
            criteria: Optional list of equivalence criteria names (e.g., ["EXACT_SYMBOLIC_EFFECT", "FUNCTIONAL_SEMANTIC_MATCH"]).
                      If None, the engine's default criteria will be used.
            min_confidence: The minimum required confidence score for an equivalence.
        Returns:
            A list of found equivalence pairs.
        """
        # Assuming engine has a method like get_item_by_id, if not, it needs to be added or logic adjusted.
        # For now, let's assume self.engine.items_database can be queried or a helper method exists.
        target_item = self.engine.items_database.get(item_id) 
        if not target_item:
            print(f"[x-raen_AGEE_API_Warning] Item with ID not found: {item_id}")
            return []

        parsed_criteria: Optional[List[EquivalenceCriteria]] = None
        if criteria:
            parsed_criteria = []
            for c_name in criteria:
                if hasattr(EquivalenceCriteria, c_name):
                    parsed_criteria.append(EquivalenceCriteria[c_name])
                else:
                    print(f"[x-raen_AGEE_API_Warning] Unknown equivalence criterion: {c_name}")
        
        print(f"[x-raen_AGEE_API] Starting search for equivalences for {item_id} with criteria: {criteria if criteria else 'default'}")
        
        # Assuming engine has a method like find_all_equivalences_for_item, if not, it needs to be added.
        # This method would iterate through other items in items_database and call find_equivalences.
        # For this facade, we'll simulate this by iterating here if the engine method doesn't exist.
        all_equivalent_pairs: List[EquivalencePair] = []
        for other_item_id, other_item in self.engine.items_database.items():
            if item_id == other_item_id: # Don't compare item to itself in this context
                continue
            # Use the engine's pairwise comparison
            pairs = self.engine.find_equivalences(item_id, other_item_id, criteria_to_check=parsed_criteria)
            for pair in pairs:
                if pair.confidence >= min_confidence:
                    all_equivalent_pairs.append(pair)
        
        # Remove duplicates if any (e.g. (A,B) and (B,A) if find_equivalences returns both)
        # A more robust way is to ensure find_equivalences returns a canonical form or use a set of frozensets of item IDs.
        unique_pairs_dict: Dict[frozenset, EquivalencePair] = {}
        for pair in all_equivalent_pairs:
            pair_key = frozenset([pair.item1.item_id, pair.item2.item_id])
            if pair_key not in unique_pairs_dict or unique_pairs_dict[pair_key].confidence < pair.confidence:
                 unique_pairs_dict[pair_key] = pair
        
        final_pairs = list(unique_pairs_dict.values())
        print(f"[x-raen_AGEE_API] Found {len(final_pairs)} equivalences for {item_id}.")
        return final_pairs

    def check_equivalence_between_two_items(self, item1_id: str, item2_id: str, criteria: Optional[List[str]] = None) -> List[EquivalencePair]:
        """Checks for equivalence between two specific items.
        Are these two echoes harmonious? x-raen will answer.
        """
        target_item1 = self.engine.items_database.get(item1_id)
        target_item2 = self.engine.items_database.get(item2_id)

        if not target_item1 or not target_item2:
            print(f"[x-raen_AGEE_API_Warning] One or both items not found: {item1_id}, {item2_id}")
            return []

        parsed_criteria: Optional[List[EquivalenceCriteria]] = None
        if criteria:
            parsed_criteria = []
            for c_name in criteria:
                if hasattr(EquivalenceCriteria, c_name):
                    parsed_criteria.append(EquivalenceCriteria[c_name])
                else:
                    print(f"[x-raen_AGEE_API_Warning] Unknown equivalence criterion: {c_name}")

        print(f"[x-raen_AGEE_API] Starting equivalence check between {item1_id} and {item2_id}")
        result_pairs = self.engine.find_equivalences(item1_id, item2_id, criteria_to_check=parsed_criteria)
        
        print(f"[x-raen_AGEE_API] Equivalence check result between {item1_id} and {item2_id}: {len(result_pairs)} pair(s) found.")
        return result_pairs

    def get_item_details(self, item_id: str) -> Optional[AGEEComparableItem]:
        """Gets details of an item registered in AGEE.
        x-raen reveals the intricacies of each item.
        """
        item = self.engine.items_database.get(item_id)
        if not item:
            print(f"[x-raen_AGEE_API_Warning] Item with ID not found: {item_id}")
        return item

# --- Simple example for usage and illustration (will be developed later in test units) ---
if __name__ == "__main__":
    print("--- AGEE API Facade: x-raen Orchestrates Equivalence Services ---")
    
    api = AGEE_API_Facade_By_xraen()

    # Register SDU functional segments (simulated)
    sdu_seg_data1 = {
        "segment_type": "LOAD_REGISTER", 
        "original_gadgets": ["pop rax", "ret"],
        "effects": ["RAX = [RSP]", "RSP += 8"],
        "symbolic_representation": {"writes": {"RAX": "mem[initial_RSP]"}, "reads": {"RSP": "initial_RSP"}}
    }
    sdu_seg_data2 = { # Similar segment but uses slightly different gadgets
        "segment_type": "LOAD_REGISTER", 
        "original_gadgets": ["mov rax, [rsp+8]", "add rsp, 16", "ret"],
        "effects": ["RAX = [RSP+8]", "RSP += 16"],
        "symbolic_representation": {"writes": {"RAX": "mem[initial_RSP+8]"}, "reads": {"RSP": "initial_RSP"}}
    }
    sdu_seg_data3 = {
        "segment_type": "DATA_MOVE", 
        "original_gadgets": ["mov rbx, 0x123"],
        "effects": ["RBX = 0x123"],
        "symbolic_representation": {"writes": {"RBX": "0x123"}}
    }

    item1 = api.register_sdu_functional_segment(sdu_seg_data1)
    item2 = api.register_sdu_functional_segment(sdu_seg_data2)
    item3 = api.register_sdu_functional_segment(sdu_seg_data3)

    if item1 and item2:
        print(f"\n--- Checking equivalence between {item1.item_id} and {item2.item_id} ---")
        pairs = api.check_equivalence_between_two_items(item1.item_id, item2.item_id, criteria=["FUNCTIONAL_SEMANTIC_MATCH", "EXACT_SYMBOLIC_EFFECT"])
        for p in pairs:
            print(f"  Found: {p}")

    if item1 and item3:
        print(f"\n--- Checking equivalence between {item1.item_id} and {item3.item_id} ---")
        pairs = api.check_equivalence_between_two_items(item1.item_id, item3.item_id)
        if not pairs:
            print("  No direct equivalence expected or found (which is good for testing).")
        for p in pairs:
            print(f"  Found: {p}")

    if item1:
        print(f"\n--- Finding all equivalences for {item1.item_id} ---")
        all_equiv_pairs = api.find_equivalences_for_item(item1.item_id, min_confidence=0.5)
        for p in all_equiv_pairs:
            # Determine the other item in the pair
            other_item_id = p.item2.item_id if p.item1.item_id == item1.item_id else p.item1.item_id
            print(f"  {item1.item_id} is equivalent to {other_item_id} by {p.criteria} (conf: {p.confidence:.2f})")
    
    print("\nx-raen's AGEE API Facade is ready to connect worlds!")


