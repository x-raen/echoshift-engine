# RPU: Chain Assembler - x-raen's Forge for Final ROP/JOP Chains

"""
This module, crafted by x-raen, is responsible for the final assembly of ROP/JOP chains.
It takes processed functional segments, any necessary glue code, and applies final patches
to construct an executable sequence of gadgets, ready for deployment.
"""

from typing import List, Dict, Any, Optional, Tuple

class ChainAssembler_xraen:
    def __init__(self, target_info: Dict[str, Any]):
        """
        Initializes the Chain Assembler.
        target_info: Information about the target environment (e.g., architecture, bad chars).
        """
        self.target_info = target_info
        print(f"[x-raen_RPU_ChainAssembler] ChainAssembler initialized for target: {self.target_info}")

    def assemble_final_chain(
        self,
        processed_segments: List[Dict[str, Any]], 
        glue_codes_map: Optional[Dict[Tuple[str, str], List[str]]] = None, 
        final_patches: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[str], str]:
        """
        Assembles the processed functional segments, glue codes, and final patches
        to form the final executable ROP/JOP chain.

        Args:
            processed_segments: A list of processed functional segments. Each segment is a dict
                                containing at least 'id' (str) and 'gadgets' (List[str]).
                                Example: [{'id': 'seg1', 'gadgets': ['0x1', '0x2']}, {'id': 'seg2', 'gadgets': ['0x3']}]
            glue_codes_map (Optional): A dictionary containing glue codes to be inserted between specific segments.
                                       Example: {('seg1', 'seg2'): ['0x100', '0x101']} means insert these gadgets between seg1 and seg2.
            final_patches (Optional): Final patches to be applied to the chain (this might be better handled in PatchingEngine).

        Returns:
            Tuple[List[str], str]: 
                - The final chain as a list of gadget addresses/strings.
                - A report string on the assembly process.
        """
        print(f"[x-raen_RPU_ChainAssembler] assemble_final_chain called.")
        print(f"  Processed segments count: {len(processed_segments)}")
        print(f"  Glue codes map: {glue_codes_map}")
        print(f"  Final patches: {final_patches}")

        final_chain: List[str] = []
        assembly_report_parts: List[str] = ["x-raen Chain Assembly Report:"]
        
        # Actual logic will involve:
        # 1. Iterating through processed segments in order.
        # 2. Before adding the current segment's gadgets, check if glue code is needed between the previous and current segment.
        #    - If so, add the glue code gadgets first.
        # 3. Add the current segment's gadgets to the final chain.
        # 4. (Optional, or handled by PatchingEngine) Apply any final chain-level patches.
        # 5. Convert the chain to the final desired format (e.g., list of numeric addresses if currently strings).

        last_segment_id: Optional[str] = None
        for i, segment_data in enumerate(processed_segments):
            current_segment_id = segment_data.get('id')
            current_segment_gadgets = segment_data.get('gadgets', [])

            if not current_segment_id or not isinstance(current_segment_gadgets, list):
                assembly_report_parts.append(f"Warning: Segment {i} (data: {segment_data}) has invalid format and was skipped.")
                continue

            # Check for glue code between the previous and current segment
            if last_segment_id and glue_codes_map and (last_segment_id, current_segment_id) in glue_codes_map:
                glue = glue_codes_map[(last_segment_id, current_segment_id)]
                if isinstance(glue, list):
                    final_chain.extend(glue)
                    assembly_report_parts.append(f"Inserted {len(glue)} glue gadget(s) between {last_segment_id} and {current_segment_id}.")
                else:
                    assembly_report_parts.append(f"Warning: Glue code for ({last_segment_id}, {current_segment_id}) is not a list and was skipped.")
            
            final_chain.extend(current_segment_gadgets)
            assembly_report_parts.append(f"Added {len(current_segment_gadgets)} gadget(s) from segment {current_segment_id}.")
            last_segment_id = current_segment_id
            
        if final_patches:
            # This is conceptual; PatchingEngine might be a better place for this.
            # final_chain = self.apply_final_patches_on_chain(final_chain, final_patches)
            assembly_report_parts.append("Final patches application is conceptual here and not yet implemented.")

        # Convert addresses to integers if they are hex strings (example)
        # try:
        #     final_chain = [int(addr, 16) if isinstance(addr, str) and addr.startswith("0x") else addr for addr in final_chain]
        # except ValueError as e:
        #     assembly_report_parts.append(f"Error converting gadget addresses to int: {e}")

        if not final_chain and processed_segments:
            assembly_report_parts.append("Assembly resulted in an empty chain despite processed segments.")
        elif final_chain:
            assembly_report_parts.append("Basic chain assembly complete by x-raen.")
        else:
            assembly_report_parts.append("No segments processed or segments were empty.")

        return final_chain, "\n".join(assembly_report_parts)

if __name__ == '__main__':
    print("--- RPU Chain Assembler: x-raen's Test Bench ---")
    mock_target_info_ca = {"architecture": "x86_64", "bad_chars": "\x00"}
    assembler_xraen = ChainAssembler_xraen(mock_target_info_ca)

    # Test Case 1: Simple assembly without glue code
    segments1_ca = [
        {'id': 's1', 'gadgets': ['0x400100', '0x400102']},
        {'id': 's2', 'gadgets': ['0x400200']}
    ]
    chain1_ca, report1_ca = assembler_xraen.assemble_final_chain(segments1_ca)
    print("\n--- CA Test Case 1 --- ")
    print(f"Final Chain: {chain1_ca}")
    print(f"Report:\n{report1_ca}")
    assert chain1_ca == ['0x400100', '0x400102', '0x400200']

    # Test Case 2: Assembly with glue code
    segments2_ca = [
        {'id': 'segA', 'gadgets': ['0xA000']},
        {'id': 'segB', 'gadgets': ['0xB000']}
    ]
    glue_map2_ca = {('segA', 'segB'): ['0xAB01', '0xAB02']}
    chain2_ca, report2_ca = assembler_xraen.assemble_final_chain(segments2_ca, glue_codes_map=glue_map2_ca)
    print("\n--- CA Test Case 2 --- ")
    print(f"Final Chain: {chain2_ca}")
    print(f"Report:\n{report2_ca}")
    assert chain2_ca == ['0xA000', '0xAB01', '0xAB02', '0xB000']

    # Test Case 3: Segment with invalid format
    segments3_ca = [
        {'id': 'sX', 'gadgets': ['0xX000']},
        {'name': 'sY', 'code': ['0xY000']} # Invalid format (missing 'id' or 'gadgets' as list)
    ]
    chain3_ca, report3_ca = assembler_xraen.assemble_final_chain(segments3_ca)
    print("\n--- CA Test Case 3 --- ")
    print(f"Final Chain: {chain3_ca}")
    print(f"Report:\n{report3_ca}")
    assert chain3_ca == ['0xX000']
    assert "Warning: Segment 1" in report3_ca and "invalid format" in report3_ca

    # Test Case 4: Empty processed segments
    segments4_ca = []
    chain4_ca, report4_ca = assembler_xraen.assemble_final_chain(segments4_ca)
    print("\n--- CA Test Case 4 --- ")
    print(f"Final Chain: {chain4_ca}")
    print(f"Report:\n{report4_ca}")
    assert chain4_ca == []
    assert "No segments processed" in report4_ca

    print("\nx-raen's ChainAssembler tests completed (basic placeholders).")


