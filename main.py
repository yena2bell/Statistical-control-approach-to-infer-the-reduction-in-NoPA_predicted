import sys, itertools
import argparse
import Network_split_module

def parse_control(control_option):
    """Separate each item by ',' and add them to the dictionary in 'key:value' format."""
    control = {}
    if control_option:
        items = control_option.split(',')
        for item in items:
            node, value = item.split('=')
            control[node.strip()] = int(value.strip())
    return control



def read_structural_network_tsv_file(file_address):
    """read data of structural network tsv file and 
    return the directed signed edges as the list of tuples.
    
    returned value has the form of [('n1', '+', 'n2'), ("n1",'-','n5'), ...]
    each tuple is a directed signed edge. 
    ('n1', '+', 'n2') means that 'n1' node activates 'n2' node"""
    edges = []
    with open(file_address, 'r') as f:
        column_line_splited = f.readline().strip().split()
        from_column_index = column_line_splited.index("from")
        to_column_index = column_line_splited.index("to")
        sign_column_index = column_line_splited.index("sign")
        for line in f:
            if line.isspace():
                continue
            line = line.strip()
            line_splited = line.split('\t')
            edge = (line_splited[from_column_index],
                    line_splited[sign_column_index],
                    line_splited[to_column_index])
            edges.append(edge)
    
    return edges

if __name__ == "__main__":

    
    #ArgumentParser object
    parser = argparse.ArgumentParser(description="option processor")
    parser.add_argument('filename', type=str, help="address of network structure tsv file")
    parser.add_argument('--find_minimum_FVSs', type=lambda x: x.lower() == 'true', default=False, help="find minimum FVS by using exhaustive search.\n enter value as True or False. (default: False) example: --find_minimum_FVSs True ")
    parser.add_argument('--control', type=str, default="", help='control targets and their corresponding control states. (default: no control) example: --control "node1 name=1, node2 name=0" ')

    args = parser.parse_args()
    command_file_address = args.filename
    control = parse_control(args.control)
    find_minimum_FVSs = args.find_minimum_FVSs
    print("the file to read the network structure is ",command_file_address)
    print("control to apply the structural network is ",control)
    if find_minimum_FVSs:
        print("this algorithm will find minimum FVSs using brutal force search")
    else:
        print("this algorithm will find approximated minimum FVSs")



    edges_of_structural_network = read_structural_network_tsv_file(command_file_address)

    network_split_obj = Network_split_module.Network_structure_splited(edges_of_structural_network, find_minimum_FVSs)
    input_nodes = network_split_obj.get_input_nodes()
    reduction_of_NoPA_predicted = 0
    for Boolean_state_comb in itertools.product((0,1), repeat=len(input_nodes)):
        input_condition = {input_nodes[i]:Boolean_state for i, Boolean_state in enumerate(Boolean_state_comb)}

        NoPA_predicted_nominal_given_input_condition = network_split_obj.calculate_NoPA_prediction_given_input_condition(input_condition, {})
        NoPA_predicted_controlled_given_input_condition = network_split_obj.calculate_NoPA_prediction_given_input_condition(input_condition, control)
        reduction_of_NoPA_predicted_given_input_condition = NoPA_predicted_nominal_given_input_condition - NoPA_predicted_controlled_given_input_condition
        
        if input_condition:
            print("reduction of NoPA_predicted by control {} in input condition {} is".format(control, input_condition))
            print(reduction_of_NoPA_predicted_given_input_condition)
        
        reduction_of_NoPA_predicted += reduction_of_NoPA_predicted_given_input_condition
    
    print("reduction of NoPA_predicted by control {} is".format(control))
    print(reduction_of_NoPA_predicted)