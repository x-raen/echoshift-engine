# SDU: Instruction Semantics Knowledge Base (Enhanced by x-raen)

"""
This module, conceived and meticulously enhanced by x-raen, lays the foundational structure for the
Instruction Semantics Knowledge Base (ISKB) within the Semantic Deconstruction Unit (SDU)
of the EchoShift tool.

The ISKB is envisioned as a dynamic, comprehensive, and extensible repository detailing the
functional effects of instructions across various architectures (initially x86/x64, with future-proofing for others).
This enhanced design focuses on a richer representation of how instructions impact registers, memory, flags,
and control flow, serving as a critical cornerstone for EchoShift's unparalleled deep semantic understanding.
"""

from enum import Enum, auto
from typing import List, Dict, Any, Optional, Union

# --- Enums and Helper Classes for Semantic Representation (x-raen refinement) ---

class OperandType(Enum):
    REGISTER = auto()
    MEMORY = auto()         # Represents a memory location (e.g., [rax], [rbp-0x8])
    IMMEDIATE = auto()
    FLAG = auto()
    POINTER = auto()        # For operands that are pointers themselves (e.g., far jumps/calls)
    UNKNOWN = auto()
    # Future: SEGMENT_REGISTER, CONTROL_REGISTER, MMX_REGISTER, XMM_REGISTER, etc.

class AccessType(Enum):
    READ = auto()
    WRITE = auto()
    READ_WRITE = auto() # For operands that are both read and written (e.g., INC RAX)
    ADDRESS_CALCULATION = auto() # For operands used in address calculation but not directly read/written (e.g., LEA base/index)

class FlagEffectType(Enum):
    MODIFIED = auto()   # Flag is modified based on result (e.g., ADD instruction)
    SET = auto()        # Flag is explicitly set to 1
    CLEARED = auto()    # Flag is explicitly cleared to 0
    UNDEFINED = auto()  # Flag becomes undefined after the operation
    PRESERVED = auto()  # Flag is explicitly preserved (rarely needed, usually implicit)
    TESTED = auto()     # Flag is read/tested (e.g., by conditional jumps)

class ControlFlowType(Enum):
    NEXT = auto() # Default, sequential execution
    JUMP_DIRECT_ABSOLUTE = auto()
    JUMP_DIRECT_RELATIVE = auto()
    JUMP_INDIRECT = auto() # Jump to address in register/memory
    CALL_DIRECT_ABSOLUTE = auto()
    CALL_DIRECT_RELATIVE = auto()
    CALL_INDIRECT = auto() # Call address in register/memory
    RETURN = auto()
    CONDITIONAL_JUMP_DIRECT_RELATIVE = auto()
    CONDITIONAL_JUMP_INDIRECT = auto() # Less common, but possible
    SYSCALL_INTERRUPT = auto()
    EXCEPTION_INTERRUPT = auto()

class SemanticAction:
    """Represents a single semantic effect or property of an instruction (x-raen refinement)."""
    def __init__(self, action_type: str, **kwargs):
        self.action_type = action_type 
        # e.g., "register_transfer", "memory_read", "memory_write", "flag_update", 
        # "stack_push", "stack_pop", "control_flow_change", "arithmetic_op", "logical_op"
        self.details = kwargs

    def __repr__(self):
        return f"Action({self.action_type}, {self.details})"

class OperandEffect:
    """Detailed representation of an instruction's effect on an operand (x-raen design)."""
    def __init__(self, 
                 name: str, # e.g., "destination", "source1", "source2", "address_base"
                 op_type: OperandType, 
                 access: AccessType, 
                 value_source: Optional[str] = None, # For WRITE: "source1", "immediate", "result_of_operation:<op_name>"
                 size_bits: Optional[int] = None, # Operand size in bits
                 address_calculation_formula: Optional[str] = None, # For MEMORY: e.g., "[base_reg + index_reg*scale + displacement]"
                 is_implicit: bool = False # e.g., implicit RSP modification in PUSH
                 ):
        self.name = name
        self.op_type = op_type
        self.access = access
        self.value_source = value_source
        self.size_bits = size_bits
        self.address_calculation_formula = address_calculation_formula
        self.is_implicit = is_implicit

    def __repr__(self):
        return f"OperandEffect({self.name}, {self.op_type.name}, {self.access.name}, size={self.size_bits}bits)"

class InstructionSemantic:
    """Describes the semantics of a single instruction mnemonic (Enhanced by x-raen)."""
    def __init__(self, mnemonic: str, arch: str = "x86_64"):
        self.mnemonic = mnemonic.upper() # Normalize mnemonic
        self.arch = arch
        self.description: Optional[str] = None
        self.long_description: Optional[str] = None # For more detailed explanations
        self.categories: List[str] = [] # e.g., ["Data Transfer", "Arithmetic", "Control Flow"]
        
        self.operands: List[OperandEffect] = [] # Explicit and implicit operands
        self.flags_effects: Dict[str, FlagEffectType] = {} # e.g., {"ZF": FlagEffectType.MODIFIED}
        self.control_flow_effects: List[Dict[str, Any]] = [] # Describes how RIP is affected
        self.custom_actions: List[SemanticAction] = [] # For complex or unique behaviors not covered above

    def set_description(self, short_desc: str, long_desc: Optional[str] = None):
        self.description = short_desc
        self.long_description = long_desc if long_desc else short_desc

    def add_category(self, category: str):
        if category not in self.categories:
            self.categories.append(category)

    def add_operand(self, name: str, op_type: OperandType, access: AccessType, 
                    value_source: Optional[str] = None, size_bits: Optional[int] = None, 
                    address_formula: Optional[str] = None, implicit: bool = False):
        self.operands.append(OperandEffect(name, op_type, access, value_source, size_bits, address_formula, implicit))

    def add_flag_effect(self, flag_name: str, effect_type: FlagEffectType):
        self.flags_effects[flag_name.upper()] = effect_type

    def add_control_flow(self, cf_type: ControlFlowType, target_operand_name: Optional[str] = None, condition_flag: Optional[str] = None):
        effect = {"type": cf_type.name}
        if target_operand_name:
            effect["target_source"] = target_operand_name # Name of an operand that holds the target address
        if condition_flag:
            effect["condition_flag"] = condition_flag # e.g., "ZF"
        self.control_flow_effects.append(effect)
        if ControlFlowType.NEXT not in [cf["type"] for cf in self.control_flow_effects] and cf_type != ControlFlowType.NEXT:
            # If a non-sequential control flow is added, and NEXT isn't explicitly there, assume it might not fall through
            # This logic might need refinement based on instruction specifics (e.g. call falls through conceptually before jump)
            pass 

    def add_custom_action(self, action: SemanticAction):
        self.custom_actions.append(action)

    def __repr__(self):
       return f"InstructionSemantic({self.mnemonic}, Arch:{self.arch}, Operands:{len(self.operands)}, Flags:{len(self.flags_effects)}, CF:{len(self.control_flow_effects)})"

class InstructionSemanticsDB:
    """A more comprehensive knowledge base for instruction semantics (x-raen architecture)."""
    def __init__(self):
        self._db: Dict[str, Dict[str, InstructionSemantic]] = {} # Arch -> Mnemonic -> Semantic
        self._initialize_database()

    def _initialize_database(self):
        # Initialize for x86_64 by default
        self._db["x86_64"] = {}
        self._populate_x86_64_instructions()

    def _populate_x86_64_instructions(self):
        db_x86_64 = self._db["x86_64"]

        # MOV
        mov_sem = InstructionSemantic("MOV", "x86_64")
        mov_sem.set_description("Moves data from source to destination.")
        mov_sem.add_category("Data Transfer")
        mov_sem.add_operand(name="destination", op_type=OperandType.REGISTER, access=AccessType.WRITE, value_source="source") # Size varies
        mov_sem.add_operand(name="source", op_type=OperandType.REGISTER, access=AccessType.READ) # Or MEMORY/IMMEDIATE
        # MOV usually doesn't affect flags, except specific cases like MOV to segment register.
        mov_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[mov_sem.mnemonic] = mov_sem

        # PUSH
        push_sem = InstructionSemantic("PUSH", "x86_64")
        push_sem.set_description("Pushes a value onto the stack.")
        push_sem.add_category("Stack Operation").add_category("Data Transfer")
        push_sem.add_operand(name="source", op_type=OperandType.REGISTER, access=AccessType.READ, size_bits=64) # Or MEMORY/IMMEDIATE, size can be 16/32/64
        push_sem.add_operand(name="RSP_implicit_src", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, implicit=True, value_source="RSP - operand_size/8")
        push_sem.add_operand(name="stack_memory_implicit_dst", op_type=OperandType.MEMORY, access=AccessType.WRITE, implicit=True, value_source="source", address_formula="[RSP_new]")
        push_sem.add_custom_action(SemanticAction("stack_push", register_sp="RSP", value_operand="source"))
        push_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[push_sem.mnemonic] = push_sem

        # POP
        pop_sem = InstructionSemantic("POP", "x86_64")
        pop_sem.set_description("Pops a value from the stack into the destination.")
        pop_sem.add_category("Stack Operation").add_category("Data Transfer")
        pop_sem.add_operand(name="destination", op_type=OperandType.REGISTER, access=AccessType.WRITE, value_source="stack_top", size_bits=64) # Or MEMORY
        pop_sem.add_operand(name="RSP_implicit_src_dst", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, implicit=True, value_source="RSP + operand_size/8")
        pop_sem.add_operand(name="stack_memory_implicit_src", op_type=OperandType.MEMORY, access=AccessType.READ, implicit=True, address_formula="[RSP_old]")
        pop_sem.add_custom_action(SemanticAction("stack_pop", register_sp="RSP", target_operand="destination"))
        pop_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[pop_sem.mnemonic] = pop_sem

        # ADD
        add_sem = InstructionSemantic("ADD", "x86_64")
        add_sem.set_description("Adds source to destination and stores the result in destination.")
        add_sem.add_category("Arithmetic")
        add_sem.add_operand(name="destination", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, value_source="destination + source")
        add_sem.add_operand(name="source", op_type=OperandType.REGISTER, access=AccessType.READ) # Or IMMEDIATE/MEMORY
        for flag in ["CF", "OF", "SF", "ZF", "AF", "PF"]:
            add_sem.add_flag_effect(flag, FlagEffectType.MODIFIED)
        add_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[add_sem.mnemonic] = add_sem

        # SUB
        sub_sem = InstructionSemantic("SUB", "x86_64")
        sub_sem.set_description("Subtracts source from destination and stores the result in destination.")
        sub_sem.add_category("Arithmetic")
        sub_sem.add_operand(name="destination", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, value_source="destination - source")
        sub_sem.add_operand(name="source", op_type=OperandType.REGISTER, access=AccessType.READ) # Or IMMEDIATE/MEMORY
        for flag in ["CF", "OF", "SF", "ZF", "AF", "PF"]:
            sub_sem.add_flag_effect(flag, FlagEffectType.MODIFIED)
        sub_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[sub_sem.mnemonic] = sub_sem

        # XOR
        xor_sem = InstructionSemantic("XOR", "x86_64")
        xor_sem.set_description("Performs a bitwise XOR between source and destination, stores result in destination.")
        xor_sem.add_category("Logical")
        xor_sem.add_operand(name="destination", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, value_source="destination ^ source")
        xor_sem.add_operand(name="source", op_type=OperandType.REGISTER, access=AccessType.READ) # Or IMMEDIATE/MEMORY
        xor_sem.add_flag_effect("CF", FlagEffectType.CLEARED)
        xor_sem.add_flag_effect("OF", FlagEffectType.CLEARED)
        xor_sem.add_flag_effect("SF", FlagEffectType.MODIFIED)
        xor_sem.add_flag_effect("ZF", FlagEffectType.MODIFIED)
        xor_sem.add_flag_effect("PF", FlagEffectType.MODIFIED)
        xor_sem.add_flag_effect("AF", FlagEffectType.UNDEFINED) # AF is undefined for XOR
        xor_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[xor_sem.mnemonic] = xor_sem

        # RET
        ret_sem = InstructionSemantic("RET", "x86_64")
        ret_sem.set_description("Returns from a procedure call by popping RIP from the stack.")
        ret_sem.add_category("Control Flow").add_category("Stack Operation")
        ret_sem.add_operand(name="RSP_implicit_src_dst", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, implicit=True, value_source="RSP + ptr_size/8")
        ret_sem.add_operand(name="stack_ret_addr_implicit_src", op_type=OperandType.MEMORY, access=AccessType.READ, implicit=True, address_formula="[RSP_old]")
        ret_sem.add_control_flow(ControlFlowType.RETURN, target_operand_name="stack_ret_addr_implicit_src")
        # No ControlFlowType.NEXT after RET
        db_x86_64[ret_sem.mnemonic] = ret_sem

        # CALL (near relative/absolute for simplicity, indirect needs more operand detail)
        call_sem = InstructionSemantic("CALL", "x86_64")
        call_sem.set_description("Calls a procedure.")
        call_sem.add_category("Control Flow").add_category("Stack Operation")
        call_sem.add_operand(name="target_address", op_type=OperandType.IMMEDIATE, access=AccessType.READ) # Or REGISTER/MEMORY for indirect
        call_sem.add_operand(name="RSP_implicit_src_dst", op_type=OperandType.REGISTER, access=AccessType.READ_WRITE, implicit=True, value_source="RSP - ptr_size/8")
        call_sem.add_operand(name="stack_ret_addr_implicit_dst", op_type=OperandType.MEMORY, access=AccessType.WRITE, implicit=True, value_source="Next_RIP", address_formula="[RSP_new]")
        call_sem.add_custom_action(SemanticAction("stack_push", register_sp="RSP", value_source="Next_Instruction_Address"))
        call_sem.add_control_flow(ControlFlowType.CALL_DIRECT_RELATIVE, target_operand_name="target_address") # Or CALL_INDIRECT etc.
        # CALL implies eventual return, so conceptually execution continues after the call in the caller, but RIP changes.
        db_x86_64[call_sem.mnemonic] = call_sem

        # JMP (near relative/absolute for simplicity)
        jmp_sem = InstructionSemantic("JMP", "x86_64")
        jmp_sem.set_description("Jumps to a target address.")
        jmp_sem.add_category("Control Flow")
        jmp_sem.add_operand(name="target_address", op_type=OperandType.IMMEDIATE, access=AccessType.READ) # Or REGISTER/MEMORY for indirect
        jmp_sem.add_control_flow(ControlFlowType.JUMP_DIRECT_RELATIVE, target_operand_name="target_address") # Or JUMP_INDIRECT etc.
        db_x86_64[jmp_sem.mnemonic] = jmp_sem

        # NOP
        nop_sem = InstructionSemantic("NOP", "x86_64")
        nop_sem.set_description("No operation. Does nothing except advance RIP.")
        nop_sem.add_category("Miscellaneous")
        nop_sem.add_control_flow(ControlFlowType.NEXT)
        db_x86_64[nop_sem.mnemonic] = nop_sem

        # LEA - Load Effective Address
        lea_sem = InstructionSemantic("LEA", "x86_64")
        lea_sem.set_description("Computes an effective address from the source memory operand and stores it in the destination register.")
        lea_sem.add_category("Data Transfer").add_category("Address Calculation")
        lea_sem.add_operand(name="destination_register", op_type=OperandType.REGISTER, access=AccessType.WRITE, value_source="calculated_address_of_source_memory_operand")
        lea_sem.add_operand(name="source_memory_operand", op_type=OperandType.MEMORY, access=AccessType.ADDRESS_CALCULATION) # Memory is not read, only its address is calculated
        # LEA does not affect a
(Content truncated due to size limit. Use line ranges to read in chunks)