# SDU: Functional Segment Aggregator (Initial Design by x-raen)

"""
This module, a creative endeavor by x-raen, introduces the initial design for the
Functional Segment Aggregator (FSA) within the Semantic Deconstruction Unit (SDU)
of the EchoShift tool.

The FSA aims to analyze sequences of assembly instructions (gadgets), potentially
leveraging their semantic details and symbolic execution traces (in future versions),
to identify and group them into higher-level "Functional Segments." This abstraction
helps in understanding the purpose of gadget chains beyond individual instructions.
"""

from typing import List, Dict, Any, Optional, Tuple

# Assuming other SDU modules are accessible
from .sdu_instruction_semantics_db import InstructionSemanticsDB, InstructionSemantic, OperandType
from .sdu_functional_segments import FunctionalSegment, SegmentType, LoadRegisterSegment, StackPivotSegment, Operand, ArithmeticSegment, DataMoveSegment, ControlFlowSegment
# We might need a simple disassembler or rely on pre-parsed input for now.
# For this initial version, we'll assume gadgets are single, simple instructions for pattern matching.

class FunctionalSegmentAggregator:
    def __init__(self, semantics_db: InstructionSemanticsDB):
        self.semantics_db = semantics_db
        # More complex rules or a rule engine could be integrated here later.

    def _parse_simple_instruction(self, gadget_str: str) -> Optional[Tuple[str, List[str]]]:
        """Extremely simplified parser for a single instruction string.
        Returns (mnemonic, [operand_strings]) or None if parsing fails.
        This should be replaced by a proper disassembler (e.g., Capstone) in a real system.
        """
        gadget_str = gadget_str.strip()
        # Remove potential address prefix like "0x12345: "
        if ":" in gadget_str:
            gadget_str = gadget_str.split(":", 1)[1].strip()

        parts = gadget_str.lower().replace(",", " ").split(None, 1)
        if not parts:
            return None
        mnemonic = parts[0].upper()
        operands = []
        if len(parts) > 1:
            operands = [op.strip() for op in parts[1].split(",")] # split by comma for multiple operands
            operands = [op for op_group in operands for op in op_group.split()] # secondary split by space if any
            operands = [op for op in operands if op] # clean empty strings

        return mnemonic, operands

    def aggregate_segments(self, gadget_sequence: List[str]) -> List[FunctionalSegment]:
        """Aggregates a sequence of gadget strings into FunctionalSegments.
        This initial version uses simple pattern matching on individual gadgets.
        """
        print(f"[x-raen_FSA] Starting aggregation for {len(gadget_sequence)} gadgets.")
        aggregated_segments: List[FunctionalSegment] = []
        current_gadget_index = 0

        while current_gadget_index < len(gadget_sequence):
            gadget_str = gadget_sequence[current_gadget_index]
            parsed_instr = self._parse_simple_instruction(gadget_str)

            if not parsed_instr:
                print(f"[x-raen_FSA_WARN] Could not parse gadget: 	{gadget_str}")
                # Create a generic unknown segment for unparsable gadgets
                unknown_segment = FunctionalSegment(segment_type=SegmentType.UNKNOWN, original_gadgets=[gadget_str])
                unknown_segment.symbolic_representation = f"Unparsed: {gadget_str}"
                aggregated_segments.append(unknown_segment)
                current_gadget_index += 1
                continue

            mnemonic, operands_str = parsed_instr
            instruction_sem = self.semantics_db.get_semantics(mnemonic)
            segment_created = False

            # --- Rule-based Aggregation (Initial Simple Rules by x-raen) ---

            # Rule 1: POP REG; RET  (Simplified LoadRegisterSegment or ControlFlowSegment)
            if mnemonic == "POP" and len(operands_str) == 1:
                # Check if next instruction is RET (if available)
                is_pop_ret = False
                if current_gadget_index + 1 < len(gadget_sequence):
                    next_gadget_str = gadget_sequence[current_gadget_index + 1]
                    parsed_next_instr = self._parse_simple_instruction(next_gadget_str)
                    if parsed_next_instr and parsed_next_instr[0] == "RET":
                        is_pop_ret = True
                
                if is_pop_ret:
                    # This is a common pattern for loading a register and returning (gadget)
                    target_reg = operands_str[0].upper()
                    segment = LoadRegisterSegment(
                        original_gadgets=[gadget_str, gadget_sequence[current_gadget_index + 1]],
                        destination_register=Operand(operand_type=OperandType.REGISTER, value=target_reg),
                        source=Operand(operand_type="description", value="value from stack top, then RET")
                    )
                    segment.effects.append(f"{target_reg} = [RSP]; RIP = [[RSP+8]] (effectively); RSP += 16")
                    aggregated_segments.append(segment)
                    current_gadget_index += 2 # Consumed two gadgets
                    segment_created = True
                else:
                    # Just a POP, could be part of something else or a simple data move
                    target_reg = operands_str[0].upper()
                    segment = DataMoveSegment(
                        original_gadgets=[gadget_str],
                        destination_operand=Operand(operand_type=OperandType.REGISTER, value=target_reg),
                        source_operand=Operand(operand_type=OperandType.MEMORY, value="[RSP]")
                    )
                    segment.effects.append(f"{target_reg} = [RSP]; RSP += 8")
                    aggregated_segments.append(segment)
                    current_gadget_index += 1
                    segment_created = True
            
            # Rule 2: MOV REG, REG/IMM (DataMoveSegment)
            elif not segment_created and mnemonic == "MOV" and len(operands_str) == 2:
                dest_op_str, src_op_str = operands_str[0].upper(), operands_str[1].upper()
                # Basic operand type guessing (highly simplified)
                dest_type = OperandType.REGISTER if not dest_op_str.startswith("[") else OperandType.MEMORY
                src_type = OperandType.REGISTER if not src_op_str.startswith("[") and not src_op_str.startswith("0X") else (OperandType.IMMEDIATE if src_op_str.startswith("0X") else OperandType.MEMORY)         
                segment = DataMoveSegment(
                    original_gadgets=[gadget_str],
                    destination_operand=Operand(operand_type=dest_type, value=dest_op_str),
                    source_operand=Operand(operand_type=src_type, value=src_op_str)
                )
                segment.effects.append(f"{dest_op_str} = {src_op_str}")
                aggregated_segments.append(segment)
                current_gadget_index += 1
                segment_created = True

            # Rule 3: ADD/SUB REG, REG/IMM (ArithmeticSegment)
            elif not segment_created and mnemonic in ["ADD", "SUB"] and len(operands_str) == 2:
                dest_op_str, src_op_str = operands_str[0].upper(), operands_str[1].upper()
                dest_type = OperandType.REGISTER # Assuming register destination for arithmetic for now
                src_type = OperandType.REGISTER if not src_op_str.startswith("0X") else OperandType.IMMEDIATE

                segment = ArithmeticSegment(
                    original_gadgets=[gadget_str],
                    operation_type=mnemonic,
                    destination_operand=Operand(operand_type=dest_type, value=dest_op_str),
                    source_operands=[Operand(operand_type=src_type, value=src_op_str)]
                )
                segment.effects.append(f"{dest_op_str} = {dest_op_str} {mnemonic} {src_op_str}")
                aggregated_segments.append(segment)
                current_gadget_index += 1
                segment_created = True

            # Rule 4: RET (ControlFlowSegment)
            elif not segment_created and mnemonic == "RET" and not operands_str:
                segment = ControlFlowSegment(
                    original_gadgets=[gadget_str],
                    flow_type="return"
                )
                segment.target_description = "address from stack top"
                segment.effects.append(f"RIP = [RSP]; RSP += 8")
                aggregated_segments.append(segment)
                current_gadget_index += 1
                segment_created = True

            # Rule 5: Stack Pivot (e.g., MOV RSP, RDX; or XCHG RSP, RAX)
            elif not segment_created and mnemonic == "MOV" and len(operands_str) == 2 and operands_str[0].upper() == "RSP":
                segment = StackPivotSegment(
                    original_gadgets=[gadget_str],
                    new_stack_pointer=Operand(operand_type=OperandType.REGISTER, value=operands_str[1].upper())
                )
                segment.effects.append(f"RSP = {operands_str[1].upper()}")
                aggregated_segments.append(segment)
                current_gadget_index += 1
                segment_created = True
            elif not segment_created and mnemonic == "XCHG" and len(operands_str) == 2 and "RSP" in [o.upper() for o in operands_str]:
                other_reg = operands_str[1].upper() if operands_str[0].upper() == "RSP" else operands_str[0].upper()
                segment = StackPivotSegment(
                    original_gadgets=[gadget_str],
                    new_stack_pointer=Operand(operand_type=OperandType.REGISTER, value=other_reg) # Assuming the other register becomes the new SP source
                )
                segment.effects.append(f"RSP, {other_reg} = {other_reg}, RSP")
                aggregated_segments.append(segment)
                current_gadget_index += 1
                segment_created = True

            # Default: If no specific rule matched, treat as an UNKNOWN or a generic instruction segment
            if not segment_created:
                print(f"[x-raen_FSA_INFO] Gadget 	{gadget_str}	 not matched by specific rules, creating generic segment.")
                generic_segment = FunctionalSegment(
                    segment_type=SegmentType.UNKNOWN, # Or a new SegmentType.SINGLE_INSTRUCTION
                    original_gadgets=[gadget_str]
                )
                generic_segment.symbolic_representation = f"Instruction: {mnemonic} {' '.join(operands_str) if operands_str else ''}"
                if instruction_sem and instruction_sem.description:
                    generic_segment.effects.append(instruction_sem.description)
                aggregated_segments.append(generic_segment)
                current_gadget_index += 1
        
        print(f"[x-raen_FSA] Aggregation finished. Found {len(aggregated_segments)} segments.")
        return aggregated_segments

# --- Example Usage (Illustrative - by x-raen) ---
if __name__ == "__main__":
    # Needs InstructionSemanticsDB to be initialized
    from .sdu_instruction_semantics_db import InstructionSemanticsDB
    semantics_db = InstructionSemanticsDB()
    
    aggregator = FunctionalSegmentAggregator(semantics_db)

    # Test gadget sequence
    test_chain = [
        "0x1000: pop rax",         # Should be DataMoveSegment (or part of LoadRegister if next is RET)
        "0x1001: ret",             # Forms LoadRegisterSegment with previous POP
        "0x2000: mov rbx, 0x1234", # DataMoveSegment
        "0x2005: add rax, rbx",    # ArithmeticSegment
        "0x2008: push rax",        # DataMoveSegment (push)
        "0x3000: mov rsp, rbp",    # StackPivotSegment
        "0x3003: ret",             # ControlFlowSegment
        "0x4000: xor eax, eax",    # Will be ArithmeticSegment if XOR is added to ISKB and rules
                                   # Otherwise, generic/unknown by current rules
        "invalid gadget string"    # UnknownSegment
    ]

    print("\n--- Testing FunctionalSegmentAggregator (by x-raen) ---")
    identified_segments = aggregator.aggregate_segments(test_chain)

    print("\nIdentified Functional Segments:")
    for i, segment in enumerate(identified_segments):
        print(f"  Segment {i+1}: {segment}")
        print(f"    Type: {segment.segment_type}")
        print(f"    Original Gadgets: {segment.original_gadgets}")
        if segment.effects:
            print(f"    Effects: {segment.effects}")
        if segment.symbolic_representation:
            print(f"    Symbolic Rep: {segment.symbolic_representation}")
        print("    ---")


