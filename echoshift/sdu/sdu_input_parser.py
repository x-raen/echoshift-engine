# SDU: Input Chain Parser (Enhanced by x-raen)

"""
This module, crafted by x-raen, defines the initial version of the Input Chain Parser
for the Semantic Deconstruction Unit (SDU) of the EchoShift tool.

Its purpose is to read ROP/JOP chains from various input formats and convert them
into a structured list of gadget representations, including addresses and annotations,
ready for deeper semantic analysis. This parser is designed with extensibility in mind
to support multiple formats and richer semantic information extraction in the future.
"""

from typing import List, Dict, Any, Tuple, Optional
import re

# Assuming sdu_functional_segments.py is in the same directory or accessible in PYTHONPATH
# The parser will now produce a list of dictionaries, each representing a gadget with its details.

class GadgetParseError(Exception):
    """Custom exception for errors during gadget parsing."""
    pass

ParsedGadget = Dict[str, Any] # Typedef for clarity: e.g., {"address": Optional[int], "instruction": str, "raw_line": str, "annotations": List[str]}

class BaseInputParser:
    """Base class for different input parsers."""
    def __init__(self):
        pass

    def parse(self, input_data: str) -> List[ParsedGadget]:
        """Parses the input data and returns a list of structured gadget representations."""
        raise NotImplementedError("Each parser must implement the parse method.")

    def _extract_annotations_and_clean(self, line: str) -> Tuple[str, List[str]]:
        """Extracts annotations (comments) and returns the cleaned line part and annotations list."""
        annotations: List[str] = []
        cleaned_line = line

        comment_patterns = [
            (re.compile(r"#\s*(.*)"), "#"),
            (re.compile(r"//\s*(.*)"), "//"),
            (re.compile(r";;\s*(.*)"), ";;")
        ]

        all_found_annotations = []
        for pattern, _ in comment_patterns:
            for match in pattern.finditer(line):
                all_found_annotations.append((match.start(), match.group(1).strip()))
        
        if all_found_annotations:
            all_found_annotations.sort(key=lambda x: x[0])
            split_point = all_found_annotations[0][0]
            cleaned_line = line[:split_point].strip()
            annotations = [ann_text for _, ann_text in all_found_annotations if ann_text]
        else:
            cleaned_line = line.strip()

        return cleaned_line, annotations

class SimpleTextParser(BaseInputParser):
    """Parses a simple text format where each line can be an address, instruction, and annotations.
    Example: `0x12345: pop rax; ret // Load value into rax`
    Lines starting with typical comment markers (if they are the *only* thing on the line after stripping) are ignored.
    Empty lines are ignored.
    """
    def parse(self, input_data: str) -> List[ParsedGadget]:
        parsed_gadgets: List[ParsedGadget] = []
        lines = input_data.splitlines()
        address_instr_pattern = re.compile(r"^\s*(?:(0x[0-9a-fA-F]+|[a-fA-F0-9]+h)\s*[:\s]\s*)?(.*)", re.IGNORECASE)

        for line_number, raw_line in enumerate(lines, 1):
            instruction_part, annotations = self._extract_annotations_and_clean(raw_line)

            if not instruction_part:
                if annotations and raw_line.strip().startswith(tuple([p[1] for p in self._get_comment_markers()])):
                    continue
                elif not raw_line.strip():
                    continue
                continue

            match = address_instr_pattern.match(instruction_part)
            if match:
                address_str = match.group(1)
                instruction_text = match.group(2).strip()
                parsed_address: Optional[int] = None
                if address_str:
                    try:
                        if address_str.lower().endswith("h"):
                            parsed_address = int(address_str[:-1], 16)
                        else:
                            parsed_address = int(address_str, 16)
                    except ValueError:
                        instruction_text = instruction_part

                if not instruction_text:
                    if annotations:
                        pass
                    continue

                if instruction_text:
                    gadget_info: ParsedGadget = {
                        "address": parsed_address,
                        "instruction": instruction_text,
                        "raw_line": raw_line,
                        "annotations": annotations
                    }
                    parsed_gadgets.append(gadget_info)
            else:
                if instruction_part:
                    gadget_info: ParsedGadget = {
                        "address": None,
                        "instruction": instruction_part,
                        "raw_line": raw_line,
                        "annotations": annotations
                    }
                    parsed_gadgets.append(gadget_info)
        return parsed_gadgets

    def _get_comment_markers(self) -> List[Tuple[re.Pattern, str]]:
        return [
            (re.compile(r"^\s*#"), "#"),
            (re.compile(r"^\s*//"), "//"),
            (re.compile(r"^\s*;;"), ";;") # Corrected from ;;-
        ]

class PsfreeLapseJsParser(BaseInputParser):
    """(Conceptual) Parser for JavaScript Map format used in psfree-lapse.
    This parser is a placeholder and needs a robust JS parsing mechanism for production use.
    Output format is List[ParsedGadget] for consistency.
    """
    def parse(self, input_data: str) -> List[ParsedGadget]:
        print("[x-raen_INFO] PsfreeLapseJsParser is currently conceptual and uses naive extraction.")
        parsed_gadgets: List[ParsedGadget] = []
        # Regex for: `[0xADDRESS, "INSTRUCTION"], // ANNOTATION` or `0xADDRESS: "INSTRUCTION", // ANNOTATION`
        # This regex is illustrative and may need refinement for actual JS map structures.
        pattern = re.compile(r"(?:0x[0-9a-fA-F]+|\[\s*0x([0-9a-fA-F]+))\s*[,:]\s*\"([^\"]+)\"", re.IGNORECASE)
        
        lines = input_data.splitlines()
        for line_number, raw_line in enumerate(lines, 1):
            instruction_part, annotations = self._extract_annotations_and_clean(raw_line) # JS comments are //
            
            match = pattern.search(instruction_part)
            if match:
                try:
                    # Group 1 might be from the [0xADDRESS,... form, group 2 from 0xADDRESS: ... form
                    address_str = match.group(1) if match.group(1) else match.group(0) # Fallback to whole match for address if group 1 is empty
                    # Refine address extraction if group 1 is not the address directly
                    addr_match = re.search(r"0x([0-9a-fA-F]+)", address_str)
                    if addr_match:
                        address = int(addr_match.group(1), 16)
                        instruction = match.group(2).strip() # Group 2 is usually the instruction string
                        parsed_gadgets.append({
                            "address": address,
                            "instruction": instruction,
                            "raw_line": raw_line,
                            "annotations": annotations
                        })
                    else:
                        print(f"[x-raen_WARN] PsfreeLapseJsParser: Could not extract address from matched part: {address_str} in line: {raw_line}")                        
                except ValueError:
                    print(f"[x-raen_WARN] PsfreeLapseJsParser: ValueError parsing line: {raw_line}")
                except IndexError:
                    print(f"[x-raen_WARN] PsfreeLapseJsParser: IndexError parsing line (check regex groups): {raw_line}")                    
        
        if not parsed_gadgets and input_data.strip():
            print("[x-raen_WARN] Naive JS parsing found no gadgets. Input might be too complex or not match expected simple pattern.")
        return parsed_gadgets

class ROPGadgetParser(BaseInputParser):
    """Parses the output format of the ROPgadget tool.
    Example ROPGadget line: `0x00000000004011aa : pop rdi ; ret`
    It also handles and extracts potential annotations if added manually to ROPGadget output.
    """
    def parse(self, input_data: str) -> List[ParsedGadget]:
        parsed_gadgets: List[ParsedGadget] = []
        lines = input_data.splitlines()

        # ROPGadget format: 0xADDRESS : INSTRUCTION_SEQUENCE
        # Annotations can be at the end, handled by _extract_annotations_and_clean
        gadget_line_pattern = re.compile(r"^\s*(0x[0-9a-fA-F]+)\s*:\s*(.*)", re.IGNORECASE)

        # Skip common header/footer lines from ROPGadget
        skip_patterns = [
            re.compile(r"^Gadgets found by ROPgadget", re.IGNORECASE),
            re.compile(r"^=+\s*$"), # Separator line like =====
            re.compile(r"^Unique gadgets found:", re.IGNORECASE)
        ]

        for line_number, raw_line in enumerate(lines, 1):
            # Check if the line should be skipped
            if any(skip_pattern.match(raw_line.strip()) for skip_pattern in skip_patterns):
                continue

            instruction_part, annotations = self._extract_annotations_and_clean(raw_line)

            if not instruction_part:
                if annotations and raw_line.strip().startswith(tuple([p[1] for p in self._get_comment_markers()])):
                    continue # Full comment line
                elif not raw_line.strip():
                    continue # Empty line
                continue

            match = gadget_line_pattern.match(instruction_part)
            if match:
                address_str = match.group(1)
                instruction_text = match.group(2).strip()
                
                parsed_address: Optional[int] = None
                if address_str:
                    try:
                        parsed_address = int(address_str, 16)
                    except ValueError:
                        # This should not happen if gadget_line_pattern matched correctly
                        print(f"[x-raen_WARN] ROPGadgetParser Line {line_number}: Invalid address format 	'{address_str}". This is unexpected.")
                        # Treat as instruction without address if parsing fails, though unlikely for this pattern
                        instruction_text = instruction_part 
                        parsed_address = None
                
                if instruction_text: # Ensure instruction is not empty
                    gadget_info: ParsedGadget = {
                        "address": parsed_address,
                        "instruction": instruction_text,
                        "raw_line": raw_line,
                        "annotations": annotations
                    }
                    parsed_gadgets.append(gadget_info)
                # else: (Instruction text is empty after address and colon, e.g. "0x123 : ")
                #    print(f"[x-raen_WARN] ROPGadgetParser Line {line_number}: No instruction found after address and colon: {raw_line}")
            else:
                # If it's not a gadget line, and not a skipped line, and not a full comment line, what is it?
                # It could be a line that _extract_annotations_and_clean fully consumed if it was only a comment.
                # Or it could be an unparseable line. For now, if instruction_part is non-empty, we treat it as an addressless gadget.
                # This might be too lenient for ROPGadget output which is quite structured.
                if instruction_part: # If there's something left after cleaning comments, and it didn't match ROPGadget format
                    # print(f"[x-raen_INFO] ROPGadgetParser Line {line_number}: Line does not match ROPGadget format, treating as addressless gadget: 	'{instruction_part}". Raw: 	'{raw_line}")
                    # This behavior might need refinement. For strict ROPGadget parsing, non-matching lines could be errors or ignored.
                    # For now, let's be consistent with SimpleTextParser's fallback for addressless lines.
                    gadget_info: ParsedGadget = {
                        "address": None,
                        "instruction": instruction_part,
                        "raw_line": raw_line,
                        "annotations": annotations
                    }
                    parsed_gadgets.append(gadget_info)
        return parsed_gadgets

    def _get_comment_markers(self) -> List[Tuple[re.Pattern, str]]:
        "Helper to get comment patterns, used for identifying full comment lines." 
        return [
            (re.compile(r"^\s*#"), "#"),
            (re.compile(r"^\s*//"), "//"),
            (re.compile(r"^\s*;;"), ";;")
        ]

# --- Input Parser Factory (x-raen's design for flexibility) ---
class InputParserFactory:
    @staticmethod
    def get_parser(format_type: str) -> BaseInputParser:
        if format_type.lower() == "simple_text":
            return SimpleTextParser()
        elif format_type.lower() == "ropgadget":
            return ROPGadgetParser()
        elif format_type.lower() == "psfree_lapse_js":
            return PsfreeLapseJsParser() # Still conceptual
        # Add other parsers here, e.g., for JSON, XML, specific tool outputs
        # elif format_type.lower() == "json_chain":
        #     return JsonChainParser()
        else:
            raise ValueError(f"[x-raen_ERROR] Unknown parser format type: {format_type}")

# --- Example Usage (Illustrative - Enhanced by x-raen) ---
if __name__ == "__main__":
    print("--- Testing SimpleTextParser (by x-raen) ---")
    simple_chain_data = """
    # This is a full line comment and should be ignored
    pop rax; ret          // Annotation: Load value into rax
    0x12345: mov rdi, rax; ret # Another annotation
    pop rsi; ret ;; A third type of annotation
    ; This is another full line comment style (if supported by _get_comment_markers)
    0xabcdef: add rax, rsi; ret // Multiple // annotations // on one line (handled by extraction)
    mov [0x1000], rax ; This is a store operation
    1234h: xor eax, eax ; Address with 'h'
    """
    simple_parser = InputParserFactory.get_parser("simple_text")
    parsed_simple_gadgets = simple_parser.parse(simple_chain_data)
    print("Parsed gadgets (SimpleTextParser):")
    for i, gadget_info in enumerate(parsed_simple_gadgets):
        print(f"  Gadget {i}: Addr: {hex(gadget_info['address']) if gadget_info['address'] is not None else 'N/A'}, Instr: 	'{gadget_info['instruction']}', Annots: {gadget_info['annotations']}")

    print("\n--- Testing PsfreeLapseJsParser (Conceptual - by x-raen) ---")
    js_like_data_simple = """
    const gadgetMap = new Map([
        [0x111111, "pop rdi; ret"], // JS comment as annotation
        [0x222222, "pop rsi; ret"], // Another one
        // 0x333333: "mov rax, rdi; ret", // commented out gadget in JS
        [0x444444, "add rax, rsi; call rbx"], // And one more
    ]);
    """
    js_parser = InputParserFactory.get_parser("psfree_lapse_js")
    parsed_js_gadgets_simple = js_parser.parse(js_like_data_simple)
    print("Parsed gadgets (PsfreeLapseJsParser - simple format):")
    for i, gadget_info in enumerate(parsed_js_gadgets_simple):
        print(f"  Gadget {i}: Addr: {hex(gadget_info['address']) if gadget_info['address'] is not None else 'N/A'}, Instr: 	'{gadget_info['instruction']}', Annots: {gadget_info['annotations']}")

    print("\n--- Testing ROPGadgetParser (by x-raen) ---")
    ropgadget_output_data = """
    Gadgets found by ROPgadget v6.5
    ============================================================
    0x00000000004011aa : pop rdi ; ret // Useful for arg1
    0x00000000004011ab : pop rsi ; ret # Useful for arg2
    0x00000000004011ac : pop rdx ; ret ;; Useful for arg3
    # A comment line within ROPGadget output that should be skipped by parser logic if it's not a gadge
(Content truncated due to size limit. Use line ranges to read in chunks)