
# Enter your Python code here
import pya
import os

###################
##### configuration #####
###################
# rule is [width, space,0,0] for metal layer, [size, space,bottom layer enclosure, top layer enclosure] for hole layer
layer_rule = {"Contact":[55,55,0,0],
    "Metal1":[65,65,0,0],
    "Via1":[90,90,5,10],
    "Metal2":[100,100,0,0]
    }
layer_type = {"Contact":"trench",
    "Metal1":"trench",
    "Via1":"hole",
    "Metal2":"trench"
    }
layer_mapping = {"Poly":[41,0],
    "Contact":[39,0],
    "Metal1":[46,0],
    "Via1":[47,0],
    "Metal2":[48,0],
    "Via2":[49,0],
    "Metal3":[50,0],
    "Via3":[51,0],
    "Metal4":[52,0],
    "SOI_BC":[39,19],
    "BSCAVITY":[999,0],
    "BSM1":[999,0],
    "BSV1":[999,0],
    "BSM2":[999,0],
    "BSL1":[999,0],
    "BSL2":[999,0]
    }
layer_connection = {"Contact":["Poly","Metal1"],
    "Via1":["Metal1","Metal2"],
    "Via2":["Metal2","Metal3"],
    "Via3":["Metal3","Metal4"],
    "SOI_BC":["Metal1","BSCAVITY"],
    "BSVIA1":["BSM1","BSM2"],
    "BSL1":["BSM2","BSL2"]
    }

single_antenna_width = 80 * 1000 #40um
antenna_pole_width = 4 * 1000 #4um
antenna_pole_height = 100 * 1000 #100um
split_file = os.path.join(os.environ["HOME"], "Documents", "python_script", "input_file","antenna_split.txt")
output_gds_file = os.path.join(os.environ["HOME"], "Documents", "python_script", "output_file","antenna.gds")

#================do not change below unless you understand=============
layout = pya.Layout()

#create cell for via or contact layer
for mask_layer,mask_type in layer_type.items():
    if mask_type == "hole":
        hole_cell = layout.create_cell("cell_" + mask_layer)
        cur_layer_rule_width = layer_rule[mask_layer][0]
        cur_layer_rule_space = layer_rule[mask_layer][1]
        cur_layer_num = int(layer_mapping[mask_layer][0])
        cur_layer_datatype = int(layer_mapping[mask_layer][1])
        hole_cell.shapes(layout.layer(cur_layer_num,cur_layer_datatype)).insert(pya.Box(0,0,cur_layer_rule_width,cur_layer_rule_width))

with open(split_file) as f:
    for line in f:
        #print(sn)
        sn,device, dimension,device_type,mask_layer,sum_rule,dif_rule,split_description,g_area,s_area,d_area,b_area = line.strip().split(",")
        
        #create empty cell
        g_antenna = layout.create_cell("dut"+sn+"_gate_ant")
        s_antenna = layout.create_cell("dut"+sn+"_source_ant")
        d_antenna = layout.create_cell("dut"+sn+"_drain_ant")
        
        #get rule
        cur_layer_rule_width = layer_rule[mask_layer][0]
        cur_layer_rule_space = layer_rule[mask_layer][1]
        antenna_space = cur_layer_rule_space
        
        #get layer mapping
        cur_layer_num = int(layer_mapping[mask_layer][0])
        cur_layer_datatype = int(layer_mapping[mask_layer][1])
        
        # create single antenna
        single_antenna = layout.create_cell("dut"+sn+"_single_ant")
        if layer_type[mask_layer] == "trench":
            single_antenna.shapes(layout.layer(cur_layer_num,cur_layer_datatype)).insert(pya.Box(-single_antenna_width/2,0,single_antenna_width/2,cur_layer_rule_width))
        elif layer_type[mask_layer] == "hole":
            hole_count = single_antenna_width // (cur_layer_rule_width + cur_layer_rule_space) -1
            bottom_layer_antenna_height = cur_layer_rule_width + layer_rule[mask_layer][2] * 2
            top_layer_antenna_height = cur_layer_rule_width + layer_rule[mask_layer][3] * 2
            single_antenna_height = max(bottom_layer_antenna_height, top_layer_antenna_height)
            
            bottom_layer = layer_connection[mask_layer][0]
            top_layer = layer_connection[mask_layer][1]
            
            single_antenna.shapes(layout.layer(layer_mapping[bottom_layer][0],layer_mapping[bottom_layer][1])).insert(pya.Box(-single_antenna_width/2,single_antenna_height/2 - bottom_layer_antenna_height/2,single_antenna_width/2,single_antenna_height/2 + bottom_layer_antenna_height/2))
            single_antenna.shapes(layout.layer(layer_mapping[top_layer][0],layer_mapping[top_layer][1])).insert(pya.Box(-single_antenna_width/2,single_antenna_height/2 - top_layer_antenna_height/2,single_antenna_width/2,single_antenna_height/2 + top_layer_antenna_height/2))
            t = pya.Trans(pya.Trans.r0(),-single_antenna_width/2 +max(layer_rule[mask_layer][2],layer_rule[mask_layer][3]),single_antenna_height/2 - cur_layer_rule_width/2)
            single_antenna.insert(pya.CellInstArray(layout.cell("cell_"+mask_layer).cell_index(),t, pya.Point(cur_layer_rule_width+cur_layer_rule_space,0), pya.Point(0,0),hole_count,1))
        else:
            print("error, layer_type undefined")
            
        #create gate antenna
        g_height = float(g_area) * 1000**2 / int(single_antenna_width)
        g_antenna_count = g_height // single_antenna.bbox().height()
        t = pya.Trans(pya.Trans.r0(),0,5000)
        g_antenna.insert(pya.CellInstArray(single_antenna.cell_index(),t, pya.Point(0,0), pya.Point(0,single_antenna.bbox().height() + antenna_space),1,g_antenna_count))
        g_antenna.shapes(layout.layer(cur_layer_num,cur_layer_datatype)).insert(pya.Box(-antenna_pole_width/2,0,antenna_pole_width/2,antenna_pole_height))
        
        #create source antenna
        s_height = float(s_area) * 1000**2 / int(single_antenna_width)
        s_antenna_count = s_height // single_antenna.bbox().height()
        t = pya.Trans(pya.Trans.r0(),0,5000)
        s_antenna.insert(pya.CellInstArray(single_antenna.cell_index(),t, pya.Point(0,0), pya.Point(0,single_antenna.bbox().height() + antenna_space),1,s_antenna_count))
        s_antenna.shapes(layout.layer(cur_layer_num,cur_layer_datatype)).insert(pya.Box(-antenna_pole_width/2,0,antenna_pole_width/2,antenna_pole_height))
        
        #create drain antenna
        d_height = float(d_area) * 1000**2 / int(single_antenna_width)
        d_antenna_count = d_height // single_antenna.bbox().height()
        t = pya.Trans(pya.Trans.r0(),0,5000)
        if d_area != "0":
            d_antenna.insert(pya.CellInstArray(single_antenna.cell_index(),t, pya.Point(0,0), pya.Point(0,single_antenna.bbox().height() + antenna_space),1,d_antenna_count))
        d_antenna.shapes(layout.layer(cur_layer_num,cur_layer_datatype)).insert(pya.Box(-antenna_pole_width/2,0,antenna_pole_width/2,antenna_pole_height))
            
layout.write(output_gds_file)