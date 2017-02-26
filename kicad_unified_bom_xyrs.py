#!/usr/bin/env python2
"""
    @package
    Generate a unified BOM and XYRS CSV file.
    Example fields:
         ['Reference',
          'Value',
          'Description',
          'Footprint',
          'PosX',
          'PosY',
          'Rotation',
          'Side',
          'MFR',
          'MPN',
          'Datasheet',
          ]
"""
#
# Generate a unified bill of materials that reads MFR and MPN fields from
# schematic components (via netlist) and puts them on the same line as XYRS
# data read from pcb file.
#
# How to use:
# 1. Place MFN (manufacturer) and MPN (manufacturer part number) in each and 
#    every schematic part.
# 2. Generate a netlist and layout board.
# 3. Add a BOM plugin specifying the path to this file
# 4. Automagically get back a unified BOM + XYRS

from __future__ import print_function

import csv
import re
import os
import string
import sys

# Import the KiCad python helper module, if not in same directory
#sys.path.append('/usr/share/doc/kicad/scripts/bom-in-python')
import kicad_netlist_reader

# pcbnew currently forces this to use python2 :(
import pcbnew

#
# Footprint and reference patterns to prune from BOM + XYRS
#
prune = {
        'footprint':['.*NetTie.*'],
        'ref':['TP.*', 'MECH.*']
        }


# Module attribute definitions from `enum MODULE_ATTR_T`
# https://github.com/KiCad/kicad-source-mirror/blob/d6097cf1aa0adc00e56cd971e427a116c503fd89/pcbnew/class_module.h#L73-L80
#
class MODULE_ATTR_T:
    MOD_DEFAULT = 0
    MOD_CMS = 1
    MOD_VIRTUAL = 2

#
# Dictoinary to hold all the magic
#
db = {}

#
# Print warnings and errors to stderr
#
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

netlist_filename = sys.argv[1]
pcb_filename = sys.argv[2]

# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
net = kicad_netlist_reader.netlist(netlist_filename)

components = net.getInterestingComponents()

compfields = net.gatherComponentFieldUnion(components)
partfields = net.gatherLibPartFieldUnion()

eprint("compfields: {}".format(compfields))
eprint("partfields: {}".format(partfields))

columnset = compfields | partfields     # union
columnset -= set(['Reference', 'Value', 'Description'])

# Ordered list with most important fields first
columns = ['Reference', 'Value', 'Description'] + sorted(columnset)

for c in components:
    ref = c.getRef()
   
    data = {
            'Reference':ref,
            'Value':c.getValue(),
            'Datasheet':c.getDatasheet(),
            'Description':c.getField('Description'),
            'Config':c.getField('Config'),
           }

    for field in columns[7:]:
        data[field] = c.getField(field)
    
    # There are footprints in the part (i.e. class) fields that are wrong or
    # blank when we only care about the footprints in the component (i.e.
    # object) fields.  Override here.
    data['Footprint'] = c.getFootprint()

    db[ref] = data
    
    #eprint('Added: {}'.format(data))

#
# Read and parse Kicad XYRS data from board file
#

if not pcb_filename:
    # Guess the pcb file name based on net list
    pcb_filename = os.path.splitext(netlist_filename)[0]+'.kicad_pcb'

board = pcbnew.LoadBoard(pcb_filename)
for module in board.GetModules():
    # Only read modules marked as NORMAL+INSERT
    if (module.GetAttributes() != MODULE_ATTR_T.MOD_CMS):
        continue

    (pos_x, pos_y) = module.GetCenter()
    side = 'top'
    if module.IsFlipped():
        side = 'bottom'

    fpid = module.GetFPID()
    fp = '{}:{}'.format(fpid.GetLibNickname(), fpid.GetFootprintName())

    data = {
            'Reference': module.GetReference(),
            'PosX': pos_x/1000000.0,
            'PosY': pos_y/1000000.0,
            'Rotation': module.GetOrientation()/10.0,
            'Side': side,
            'Footprint': fp,
            }

    ref = data['Reference']
    if ref not in db:
        eprint('[WW] PCB Skipping "{}"'.format(ref))
        continue

    for key, value in data.items():
        if key in db[ref] and value != db[ref][key]:
            eprint('[WW] PCB overriding {} {}, "{}" != "{}"'.format(ref, key, db[ref][key], value))
        db[ref][key] = value

    #eprint('Updated: {}'.format(db[ref]))


#
# Clean-up output header
#
columns_out = ['Reference',
               'Value',
               'Description',
               'Footprint',
               'PosX',
               'PosY',
               'Rotation',
               'Side',
               'MFR',
               'MPN',
               'Datasheet',
              ]

#
# Prune fields
#
ref_combined = "(" + ")|(".join(prune['ref']) + ")"
footprint_combined = "(" + ")|(".join(prune['footprint']) + ")"

for key,value in list(db.items()):
    #print("value:::: {}".format(value))
    if 'Config' in value and 'DNF' in str(value['Config']):
        del db[key]
    elif re.match(ref_combined, key):
        del db[key]
    elif 'Footprint' in value and re.match(footprint_combined, value['Footprint']):
        del db[key]

#
# Write clean output to csv based on key -> column dictionary
#
out = csv.DictWriter(sys.stdout, fieldnames=columns_out, extrasaction='ignore')
out.writerow(dict( (n,n) for n in columns_out ))

for key, value in sorted(db.items()):
    #print("entry: {}:{}".format(key, value))
    out.writerow(value)
