import os, collections, time, itertools

from Nested_canalizing_function_generator import get_nested_canalizing_functions_with_regulators_num_of
from Boolean_truthtable_calculation import Boolean_function
from Attractor_landscape_calculation_for_specific_logic_combination import Logic_combination
from Ensemble_result_read_and_analyze import Ensemble_data

class Structural_network_info:
    def __init__(self, address_structural_network_tsv_file):
        self.structural_edges = self.read_structural_network_tsv_file(address_structural_network_tsv_file)

        self.node_names = []
        self.node_regulators_map = {}
        self.node_modalities_map = {} # self.node_modalities_map[node_name][i] is the modality from node self.node_regulators_map[node_name][i] to node_name.
        self.nodename_indegree_map = {}
        self.nodes_to_perturb = []
        self.source_nodes = []
        self._parse_edges()

        self.regulator_num_nc_logics_map = {}
        self._calculate_possible_nc_logics()

    def read_structural_network_tsv_file(self, file_address):
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

    def _parse_edges(self):
        for edge in self.structural_edges:
            node_from = edge[0]
            node_to = edge[2]
            modality = edge[1]
            
            self.node_regulators_map.setdefault(node_to, []).append(node_from)
            self.node_modalities_map.setdefault(node_to, []).append(modality)
            if node_from not in self.node_names:
                self.node_names.append(node_from)
            if node_to not in self.node_names:
                self.node_names.append(node_to)
        
        # source node should have a positive self loop to avoid having an in-degree of 0.
        for node_name in self.node_names:
            if node_name not in self.node_regulators_map:
                self.node_regulators_map[node_name] = [node_name]
                self.node_modalities_map[node_name] = ['+']
        
        for node_name in self.node_names:
            # search source nodes. 
            # found source nodes are also set to have a positive self loop.
            if len(self.node_regulators_map[node_name]) == 1:
                if self.node_modalities_map[node_name] == ["+"]:
                    self.source_nodes.append(node_name)
        
        self.nodes_to_perturb = [node_name for node_name in self.node_names if node_name not in self.source_nodes]
        self.nodename_indegree_map = {node_name:len(self.node_regulators_map[node_name]) for node_name in self.node_names}

    def _calculate_possible_nc_logics(self):
        """calculate the possible nc_logics for each in-degree of the nodes in the model."""
        in_degrees = set(len(regulators) for regulators in self.node_regulators_map.values())
        for in_degree in in_degrees:
            nc_logics = get_nested_canalizing_functions_with_regulators_num_of(in_degree)
            self.regulator_num_nc_logics_map[in_degree] = nc_logics

    def get_model_regulators_order_information(self):
        """get the order of regulators for each node in the model, 
        so that the model can be restored later."""
        text = ""
        text += "node_name\tregulators_ordered\n"
        for node_name in self.node_names:
            regulators = self.node_regulators_map[node_name]
            text += "{}\t{}\n".format(node_name, '\t'.join(regulators))
        return text

    def get_nc_logics_of(self, in_degree):
        return self.regulator_num_nc_logics_map[in_degree]
        

class Ensemble_of_all_possible_nc_logics:
    def __init__(self, structural_network_info:Structural_network_info):
        self.structural_network_info = structural_network_info
        self.node_nc_logics_map = self.structural_network_info.regulator_num_nc_logics_map
        self.nodename_indegree_map = self.structural_network_info.nodename_indegree_map
        self.node_names = self.structural_network_info.node_names
        self.node_modalities_map = self.structural_network_info.node_modalities_map
        self.nodes_to_perturb = self.structural_network_info.nodes_to_perturb

        result_order = ["logic_combination","NoPA", "NoA","attractor_landscape"]
        self.perturbation_NoPA_distribution_map = collections.defaultdict(collections.Counter)
        self.perturbation_NoA_distribution_map = collections.defaultdict(collections.Counter)
        self.perturbation_textresult_map = collections.defaultdict(lambda:'\t'.join(result_order)+"\n")
        self.perturbation_textresult_refined = {}

    def _reset_perturbation_result_maps(self):
        result_order = ["logic_combination","NoPA", "NoA","attractor_landscape"]
        self.perturbation_NoPA_distribution_map = collections.defaultdict(collections.Counter)
        self.perturbation_NoA_distribution_map = collections.defaultdict(collections.Counter)
        self.perturbation_textresult_map = collections.defaultdict(lambda:'\t'.join(result_order)+"\n")
        self.perturbation_textresult_refined = {}

    def calculate_ensemble_of_all_possible_nc_logics(self, num_of_perturbation=0, folder_address=".\\", folder_name="ensemble_of_all_possible_nc_logics"):
        self._reset_perturbation_result_maps()
        self._make_save_folder(folder_address, folder_name)
        i_count = 0
        for nc_logic_comb, node_logics_map in self._make_logic_combinations():
            perturbation_nodesorder_map, perturbation_landscape_map = self._calculate_attractor_landscape_of_specific_logics(node_logics_map, num_of_perturbation)
            # `perturbation_nodesorder_map` is same regardless of `nc_logic_comb`
            # print(i_count, perturbation_nodesorder_map)
            # print(i_count, perturbation_landscape_map)
            self._analyze_and_summarize_NoPA_NoA(nc_logic_comb, perturbation_landscape_map)

            i_count += 1
            if i_count == 50:
                break
            
        self._refine_textresult_map(perturbation_nodesorder_map)
        self._save_results(folder_address, folder_name)
            

    def _make_save_folder(self, folder_address, folder_name):
        save_folder_address = os.path.join(folder_address, folder_name)
        if not os.path.exists(save_folder_address):
            os.makedirs(save_folder_address)

        with open(os.path.join(save_folder_address, "model_regulators_order_information.txt"), 'w') as f:
            f.write(self.structural_network_info.get_model_regulators_order_information())

    def _calculate_num_of_logic_combinations(self):
        nc_logics = []
        for node_name in self.node_names:
            in_degree = self.nodename_indegree_map[node_name]
            nc_logics.append(self.structural_network_info.get_nc_logics_of(in_degree))
        
        self.num_of_logic_combinations = 1
        for nc_logics_of_node in nc_logics:
            self.num_of_logic_combinations *= len(nc_logics_of_node)
        print("num of logic combinations is {}".format(self.num_of_logic_combinations))
        for i, node_name in enumerate(self.node_names):
            print("node {} has {} possible nc_logics".format(node_name, len(nc_logics[i])))

        return nc_logics

    def _make_logic_function_of_node(self, node_name, nc_logic_truthtable_integer):
        """make a logic function of the node 
        with the given nc_logic_truthtable_integer,"""
        modalities = self.node_modalities_map[node_name]
        indexes_inhibiting = [i for i, modality in enumerate(modalities) if modality == '-']
        
        def logic_function(regulator_state_array_form):
            regulator_state_array_form = regulator_state_array_form.copy()
            regulator_state_array_form[indexes_inhibiting] = 1 - regulator_state_array_form[indexes_inhibiting]
            return Boolean_function(nc_logic_truthtable_integer, regulator_state_array_form)
                
        return logic_function

    def _make_logic_combinations(self):
        """yield all possible node_function_map"""
        time_start = time.time()

        nc_logics = self._calculate_num_of_logic_combinations()
        
        num_of_logic_combs = 0
        for nc_logic_comb in itertools.product(*nc_logics):
            num_of_logic_combs += 1
            time_used = time.time()-time_start
            estimated_time = time_used/num_of_logic_combs * (self.num_of_logic_combinations - num_of_logic_combs)
            print("\r{}/{} estimated remained time: {} seconds             ".format(num_of_logic_combs, self.num_of_logic_combinations, estimated_time))
            
            node_logics_map = {}
            for i, nodename in enumerate(self.node_names):
                logic_function = self._make_logic_function_of_node(nodename, nc_logic_comb[i])
                node_logics_map[nodename] = logic_function
            yield nc_logic_comb, node_logics_map

    def _calculate_attractor_landscape_of_specific_logics(self, node_logic_map, num_of_perturbation=0):
        """for specific logic combination,
        calculate the attractor landscape of the model 
        with the given node_logic_map and num_of_perturbation."""
        obj_specific_logic = Logic_combination(self.structural_network_info, node_logic_map)
        perturbation_landscape_map = {}
        perturbation_nodesorder_map = {}
        
        for node_to_perturb in itertools.combinations(self.nodes_to_perturb, r=num_of_perturbation):
            # print("perturbation nodes: {}".format(node_to_perturb))
            for perturbed_states in itertools.product((0,1), repeat=num_of_perturbation):
                # print("perturbed states: {}".format(perturbed_states))
                perturbation_dict = dict(zip(node_to_perturb, perturbed_states))
                perturbation_tuple = tuple(zip(node_to_perturb, perturbed_states))
                
                node_names_order, landscape_calculator = obj_specific_logic.calculate_landscape_given_perturbation(perturbation_dict)
                perturbation_nodesorder_map[perturbation_tuple] = node_names_order
                perturbation_landscape_map[perturbation_tuple] = landscape_calculator.att_basin_ratio.copy()
        
        return perturbation_nodesorder_map, perturbation_landscape_map

    def _analyze_and_summarize_NoPA_NoA(self, nc_logic_comb, perturbation_landscape_map):
        for perturbation, attractor_landscape in perturbation_landscape_map.items():
            analyzed_result = self._analyze_attractor_landscape(attractor_landscape)
            line_summary = "{}\t{}".format(nc_logic_comb, self._write_attractor_landscape_to_text_form(analyzed_result, attractor_landscape))
            # print(line_summary)

            self.perturbation_NoPA_distribution_map[perturbation][analyzed_result["NoPA"]] += 1
            self.perturbation_NoA_distribution_map[perturbation][analyzed_result["NoA"]] += 1           
            self.perturbation_textresult_map[perturbation] += line_summary

    def _analyze_attractor_landscape(self, attractor_landscape):
        """caclulate NoPA and NoA from the attractor landscape"""
        analyzed_result = {"NoPA":0, "NoA":0}
        for attractor in attractor_landscape:
            analyzed_result["NoA"] += 1
            if len(attractor) == 1:
                analyzed_result["NoPA"] += 1
        return analyzed_result

    def _write_attractor_landscape_to_text_form(self, analyzed_result, attractor_landscape):
        return "{}\t{}\t{}\n".format(analyzed_result["NoPA"], analyzed_result["NoA"], attractor_landscape)

    def _refine_textresult_map(self, perturbation_nodesorder_map):
        for perturbation, textresult in self.perturbation_textresult_map.items():
            perturbation_dict = {node:state for node, state in perturbation}
            nodes_order = perturbation_nodesorder_map[perturbation]
            NoPA_distribution = dict(self.perturbation_NoPA_distribution_map[perturbation])
            NoA_distribition = dict(self.perturbation_NoA_distribution_map[perturbation])
            textresult = self.perturbation_textresult_map[perturbation]

            self.perturbation_textresult_refined[perturbation] = "perturbation:\t{}\nnode_order:\t{}\nNoPA_distribution:\t{}\nNoA_ditribution:\t{}\n{}".format(perturbation_dict, nodes_order, NoPA_distribution, NoA_distribition, textresult)

    def _convert_perturbation_tuple_to_str(self, perturbation_tuple):
        """convert perturbation_tuple to str type"""
        if not perturbation_tuple:
            return "no_perturbation"
        list_form = list(perturbation_tuple)
        list_form.sort(key=lambda x:x[0])
        list_form = ["{}_{}".format(*t) for t in list_form]
        return "__".join(list_form)

    def _save_results(self, folder_address, folder_name):
        save_folder = os.path.join(folder_address, folder_name)
        for perturbation_tuple_form, result in self.perturbation_textresult_refined.items():
            perturbation_str_form = self._convert_perturbation_tuple_to_str(perturbation_tuple_form)
            with open(os.path.join(save_folder, "{}.tsv".format(perturbation_str_form)),'w') as f:
                f.write(result)

        
if __name__ == "__main__":
    address_toy_net_links = os.path.join(r"..\example_structural_networks","Structural_network_in_Fig1.tsv")
    structural_network_info = Structural_network_info(address_toy_net_links)
    ensemble_of_all_possible_nc_logics = Ensemble_of_all_possible_nc_logics(structural_network_info)

    ensemble_of_all_possible_nc_logics.calculate_ensemble_of_all_possible_nc_logics(0)
    # calculate nominal NoPA
    ensemble_of_all_possible_nc_logics.calculate_ensemble_of_all_possible_nc_logics(1)
    # calculate perturbed NoPA with 1 node perturbation

    ensemble_data = Ensemble_data()
    selected_logic_comb = (128, 128, 128, 8, 224, 254)
    ensemble_data.draw_true_ava_NoPA_scatter_plot(selected_logic_comb)