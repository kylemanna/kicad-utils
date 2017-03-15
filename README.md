# kicad-utils
Miscellaneous utilities for Kicad

## Unified XYRS + BOM

The [`kicad_unified_bom_xyrs.py`](kicad_unified_bom_xyrs.py) script generates a unified bill of materials that reads MFR and MPN fields from schematic components (via XML netlist) and puts them on the same line as XYRS placement data read from PCB file.

This has been tested with [PCB:NG](http://www.pcb.ng/) to create a one shot BOM + Placement file to upload with gerbers in the same zip file.

### How to Use

1. Place `MFN` (manufacturer) and `MPN` (manufacturer part number) fields in each and every schematic part.
2. (Optional) Add a `Config` field and set it to `DNF` for parts you don't want fitted (aka Do Not Fit) 
3. Generate a netlist, import the net list and layout the PCB as you normally would.
4. Set the `Normal+Insert` property on parts you want placed or they won't have XYRS data.
5. Add a BOM plugin specifying the path to [`kicad_unified_bom_xyrs.py`](kicad_unified_bom_xyrs.py) file.
6. Automagically find a unified BOM + XYRS in the gerber `output_directory` set in the PCB file.  
