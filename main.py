import itertools, os
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

def get_node_and_specific_logic_files(folder_address):
    """After receiving the address of the folder containing files with specific logic information, 
    match each file's address with the corresponding node name. 
    Each file name must exactly match one of the node names used 
    in the structural network model."""
    node_specificlogicfile_map = {}
    specific_logic_files = os.listdir(folder_address)
    for specific_logic_file in specific_logic_files:
        node_name = os.path.splitext(specific_logic_file)[0]
        node_specificlogicfile_map[node_name] = os.path.join(folder_address, specific_logic_file)
    
    return node_specificlogicfile_map


def load_specific_logic(file_for_specific_logic):
    """Read the file containing specific logic information for a particular node, 
    extracting the regulator order and logic function.
    
    The first line should be formatted as 
    'regulators order: regulator_0, regulator_1, ... regulator_n'.
    Here, each regulator_i must match the node name of the corresponding regulator node 
    in the structural network model.
    
    Below the second line, 
    write the specific logic of the node in Python function definition format. 
    This function should take a numpy array of the same length as the number of regulators as its argument, 
    and return either 1 or 0. 
    Here, the i-th element of the argument array (array_argument[i]) should correspond 
    to the state of the i-th regulator (regulator_i) as listed in the first line."""
    with open(file_for_specific_logic, 'r') as file:
        # read first line, convert str after 'regulators order: ' to tuple form
        first_line = file.readline().strip()
        regulator_order = (first_line.replace("regulators order:", "").strip().split(","))
        regulator_order = tuple(regulator.strip() for regulator in regulator_order)
        
        # read the function definition and convert it to object
        function_code = file.read()
        local_scope = {}
        exec(function_code, {}, local_scope)
        
        # Finding the defined function (when the function name is not given)
        function_variable = next((v for v in local_scope.values() if callable(v)), None)
        
    return regulator_order, function_variable

if __name__ == "__main__":

    
    #ArgumentParser object
    parser = argparse.ArgumentParser(description="option processor")
    parser.add_argument('filename', type=str, help="address of network structure tsv file")
    parser.add_argument('--find_minimum_FVSs', type=lambda x: x.lower() == 'true', default=False, help="find minimum FVS by using exhaustive search.\n enter value as True or False. (default: False) example: --find_minimum_FVSs True ")
    parser.add_argument('--control', type=str, default="", help='control targets and their corresponding control states. (default: no control) example: --control "node1 name=1, node2 name=0" ')
    parser.add_argument('--set_specific_logics', type=str, default=" ", help='If you know the specific logics for certain nodes, you can use these logics to improve the accuracy of NoPA prediction. Enter the address of the folder containing files with specific logic information for each node after this option.')

    args = parser.parse_args()
    command_file_address = args.filename
    control = parse_control(args.control)
    find_minimum_FVSs = args.find_minimum_FVSs
    specific_logics_folder = args.set_specific_logics
    print(specific_logics_folder, specific_logics_folder.isspace())
    print("the file to read the network structure is ",command_file_address)
    print("control to apply the structural network is ",control)
    if find_minimum_FVSs:
        print("this algorithm will find minimum FVSs using brutal force search")
    else:
        print("this algorithm will find approximated minimum FVSs")
    if not specific_logics_folder.isspace():
        node_specificlogicfile_map = get_node_and_specific_logic_files(specific_logics_folder)
        print("logic information of nodes {} are used".format(list(node_specificlogicfile_map.keys())))
    else:
        node_specificlogicfile_map = {}


    edges_of_structural_network = read_structural_network_tsv_file(command_file_address)

    network_split_obj = Network_split_module.Network_structure_splited(edges_of_structural_network, find_minimum_FVSs)
    
    if node_specificlogicfile_map:
        for node, specific_logic_file in node_specificlogicfile_map.items():
            regulator_order, specific_logic_function = load_specific_logic(specific_logic_file)
            network_split_obj.set_specific_logic_to_node(node, regulator_order, specific_logic_function)

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