# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 09:20:34 2022

@author: jwKim
"""
import itertools

import FVS_finding_module

class Block:
    def __init__(self, nodes_regulators, nodes_to_analyze, edges, node_obj_map):
        self.nodenames_regulators = list(nodes_regulators)
        self.nodenames_to_analyze = list(nodes_to_analyze)
        self.edges_subnet = self._extract_subnet_edges(edges)
        self.node_obj_map = self._filter_node_obj_map(node_obj_map)
        
        self.node_regulators_map = {}
        self.node_activating_regulators_map = {}
        self.node_inhibiting_regulators_map = {}
        self.node_targets_map = {}
        self.node_activating_targets_map = {}
        self.node_inhibiting_targets_map = {}
        # When a given edge (X, sign, Y) is provided, 
        # X is called the regulator of Y, and Y is called the target of X.
        self._get_maps_of_links()
        
        self.num_of_possible_logic_combinations = None
        
    def _extract_subnet_edges(self, edges):
        """Only select the edges between nodes that belong to 
        'nodenames_regulators' and 'nodenames_to_analyze'"""
        edges_subnet = []
        node_names_all = set(self.nodenames_regulators+self.nodenames_to_analyze)
        for edge in edges:
            if (edge[0] in node_names_all) and (edge[-1] in node_names_all):
                edges_subnet.append(edge)
        return edges_subnet
    
    def _filter_node_obj_map(self, node_obj_map):
        """Filter out only the (node, object) pairs recorded in 'node_obj_map' 
        where the node is included in 'self.nodenames_to_analyze'."""
        node_obj_map_filtered = {node_name:node_obj_map[node_name] for node_name in self.nodenames_to_analyze}
        return node_obj_map_filtered
    
    def _get_maps_of_links(self):        
        for edge in self.edges_subnet:
            regulator = edge[0]
            target = edge[-1]
            sign = edge[1]
            
            self.node_regulators_map.setdefault(target, set()).add(regulator)
            self.node_targets_map.setdefault(regulator, set()).add(target)
            if sign == "+":
                self.node_activating_regulators_map.setdefault(target, set()).add(regulator)
                self.node_activating_targets_map.setdefault(regulator, set()).add(target)
            else:#sign == "-"
                self.node_inhibiting_regulators_map.setdefault(target, set()).add(regulator)
                self.node_inhibiting_targets_map.setdefault(regulator, set()).add(target)
    
    def get_nodes_to_analyze(self):
        return list(self.nodenames_to_analyze)
    
    def get_regulator_nodes(self):
        return list(self.nodenames_regulators)
    
    def calculate_EAVs_of_nodes_and_NoPA_predicted(self, regulators_EAV_map:"{nodename: EAV}"):
        """This method should be overridden for use in each subclass.
        
        EAV is abbreviation of Ensemble Average Value"""
        raise Exception("this method should be overridden")
    
    def _get_layers_of_acyclic_form_given_FVS_and_regulators(self, FVS_and_regulators_of_block:list):
        """SCC is separated based on the nodes in the FVS to create an acyclic form. 
        Then, the nodes of that acyclic form are classified by layer. 
        The source nodes of the acyclic network are in the top layer, 
        and the nodes that have only the top layer as their regulators belong to the next layer. 
        Nodes in the subsequent layers must have regulators only from the higher layers.

        The layers are organized as a single list containing all layers, 
        where layers with lower indices are higher layers. 
        Each layer is a list containing nodes.
        
        In the paper, each FVS node is split into sink nodes and source nodes, 
        but in the actual code, calculations are performed without splitting for convenience."""
        layers = [FVS_and_regulators_of_block]
        nodes_in_layers = set(FVS_and_regulators_of_block)
        nodes_not_yet_categorized = set(node for node in self.nodenames_to_analyze if node not in FVS_and_regulators_of_block)
        while nodes_not_yet_categorized:
            layer = []
            for node in nodes_not_yet_categorized:
                regulators = self.node_regulators_map[node]
                if regulators.issubset(nodes_in_layers):
                    layer.append(node)
            
            nodes_not_yet_categorized.difference_update(layer)
            nodes_in_layers.update(layer)
            layers.append(layer)
        
        return layers
    
    def _calculate_EAVs_given_layers(self, regulators_EAV_map, layers):
        """Given an acyclic graph in the form of layers, 
        and the 'EAV (abbreviation of Ensemble Average Value which have meaning 'probability of 1')' 
        for the source nodes (the first layer which is the layers[0]), 
        this function calculates the 'EAV' 
        for the rest of the nodes based on that.
        
        If this acyclic graph is created by splitting an SCC using FVS, 
        the FVS nodes will appear in both the first and the last layers.
        
        EAV is abbreviation of Ensemble Average Value"""
        node_EAV_map = regulators_EAV_map.copy()
        for layer in layers[1:]:
            node_EAV_map_of_layer = {}
            for node in layer:
                node_obj = self.node_obj_map[node]
                EAV_of_regulators_of_the_node = [node_EAV_map[regulator] for regulator in node_obj.regulators]
                EAV = node_obj.get_EAV_given_regulator_EAVs(EAV_of_regulators_of_the_node)
                node_EAV_map_of_layer[node] = EAV
            node_EAV_map = {**node_EAV_map, **node_EAV_map_of_layer}
            # FVS nodes are initially assigned a 'EAV' value for use in the calculations, 
            # and when the last layer is computed, 
            # they are assigned a new 'EAV' as a result of the calculation. 

            # Initially, 'node_EAV_map' contains the value used in the calculations, 
            # but after computing the last layer, 
            # this value is replaced with the newly computed 'EAV'. 

        return node_EAV_map
        
        

class Block_of_SCC(Block):
    def __init__(self, *args, **kwargs):
        if "find_minimum_FVSs" in kwargs:
            find_minimum_FVSs = kwargs["find_minimum_FVSs"]
            kwargs.pop("find_minimum_FVSs")
        else:
            find_minimum_FVSs = False
        super().__init__(*args, **kwargs)
        
        self.FVSs = []
        self._identify_FVSs(find_minimum_FVSs)
        
    def _identify_FVSs(self, find_minimum_FVS=False):
        """If 'find_minimum_FVS' is True, all minimum FVSs are calculated through exhaustive search. 
        If False, for SCCs with 15 nodes or fewer, minimum FVSs are found through exhaustive search, 
        while for larger SCCs, the SA FVSP NNS algorithm is used to calculate approximated minimum FVSs"""
        edges_subnet_except_source = []
        for edge in self.edges_subnet:
            if (edge[0] in self.nodenames_to_analyze) and (edge[-1] in self.nodenames_to_analyze):
                edges_subnet_except_source.append(edge)
        FVSs_finder = FVS_finding_module.FVS_finding(edges_subnet_except_source)
        if find_minimum_FVS:
            def find_mininum_FVSs_through_exhaustive_search(SCC, edges):
                return FVS_finding_module.FVS_brutal_force_searching()
            FVSs_finder.set_FVS_finding_strategy(find_mininum_FVSs_through_exhaustive_search)
        self.FVSs = FVSs_finder.find_FVS()
    
    def __repr__(self):
        return "Block of SCC {}".format(self.nodenames_to_analyze)
    
    def calculate_EAVs_of_nodes_and_NoPA_predicted(self, regulators_EAV_map:"{nodename: EAV}"):
        """A different acyclic form is created for each FVS. 
        Using each of these different acyclic forms, 
        the 'node_EAV_map_given_FVS' and 'NoPA_predicted_given_FVS' are calculated. 
        The calculated results are then stored 
        in 'FVS_nodeEAVmap_map' and 'FVS_NoPApredicted_map' respectively.
        
        Then, the 'NoPA_predicted_given_FVS' calculated for each FVS 
        and the 'EAV' for each node are averaged and returned.
        
        EAV is abbreviation of Ensemble Average Value"""
        FVS_nodeEAVmap_map = {}
        FVS_NoPApredicted_map = {}
        for FVS in self.FVSs:
            node_EAV_map_given_FVS, NoPA_predicted_given_FVS = self._calculate_EAVs_of_nodes_and_NoPA_predicted_given_FVS(regulators_EAV_map, FVS)
            
            # print(FVS)
            # print(node_probof1_map_given_FVS)
            # print(NoPA_predicted_given_FVS)
            # print('')
            FVS_nodeEAVmap_map[FVS] = node_EAV_map_given_FVS
            FVS_NoPApredicted_map[FVS] = NoPA_predicted_given_FVS
        
        NoPA_prediced_averaged = sum(FVS_NoPApredicted_map.values())/len(FVS_NoPApredicted_map)
        
        node_EAV_map_averaged = {}
        for node in self.nodenames_to_analyze:
            node_EAV_map_averaged[node] = 0
            for node_EAV_map in FVS_nodeEAVmap_map.values():
                node_EAV_map_averaged[node] += node_EAV_map[node]
            node_EAV_map_averaged[node] /= len(self.FVSs)
        
        return node_EAV_map_averaged, NoPA_prediced_averaged
    
    def _calculate_EAVs_of_nodes_and_NoPA_predicted_given_FVS(self, regulators_EAV_map, FVS):
        """Using the given FVS and regulators, 
        the layers of an acyclic graph are created. 
        Then, after assigning a specific state to the FVS nodes, 
        the EAV (probability of 1) for each node 
        and the PBPA (Probability of being a point attractor) are calculated.
        
        EAV is abbreviation of Ensemble Average Value"""
        regulatorsofSCC_and_FVS = tuple(regulators_EAV_map) + FVS
        layers = self._get_layers_of_acyclic_form_given_FVS_and_regulators(regulatorsofSCC_and_FVS)
        layers.append(list(FVS))
        
        FVSstate_nodeEAVmap_map = {}
        FVSstate_PBPA_map = {}
        
        for FVS_state in itertools.product((0,1), repeat=len(FVS)):
            FVS_state_map = {FVS_node:FVS_state[i] for i, FVS_node in enumerate(FVS)}
            regulators_and_FVS_EAV_map = {**regulators_EAV_map, **FVS_state_map}
            node_EAV_map_given_FVS_state = self._calculate_EAVs_given_layers(regulators_and_FVS_EAV_map, layers)
            
            # In this process, the 'EAV' for the FVS nodes in 'node_EAV_map_given_FVS_state' is 
            # not based on the values in 'FVS_state_map' but rather on the 'EAV' 
            # calculated as sink form nodes at the bottommost layer of the acyclic graph.
            
            PBPA_given_FVS_state = self._get_PBPA_given_FVS_state(FVS_state_map, node_EAV_map_given_FVS_state)
            
            FVSstate_nodeEAVmap_map[FVS_state] = node_EAV_map_given_FVS_state
            FVSstate_PBPA_map[FVS_state] = PBPA_given_FVS_state
        
        NoPA_predicted_given_FVS = sum(FVSstate_PBPA_map.values())
        node_EAV_map_given_FVS = self._get_EAVs_given_FVS(FVSstate_nodeEAVmap_map, FVSstate_PBPA_map)
        
        return node_EAV_map_given_FVS, NoPA_predicted_given_FVS
    
    def _get_EAVs_given_FVS(self, FVSstate_nodeEAVmap_map, FVSstate_PBPA_map):
        """assume that
        'FVSstate_nodeEAVmap_map'=={FVS_state1: {node1:p11, node2:p12, ...}, 
                                        FVS_state2: {node1:p21, node2:p22, ...}, ...}
        'FVSstate_PBPA_map' == {FVS_state1:q1, FVS_state2:q2, ...}
        then, 'sum_of_PBPA' == sum(q1,q2, ...) and
        'node_EAV_map' becomes {node1: (p11*q1+p21*q2+ ...)/sum_of_PBPA,
                                node2: (p12*q1+p22*q2+ ...)/sum_of_PBPA, ...}
        
        This means that each node's EAV (Ensemble Average Value which is probability of 1) is inferred for each FVS state (FVSstate_nodeEAVmap_map), 
        and based on the assumption that the inferred value is closer 
        to the actual EAV as each FVS state becomes more stable, 
        these values are weighted to infer the EAV for each node 
        across all FVS states."""
        sum_of_PBPA = 0
        node_EAV_map = {node:0 for node in self.nodenames_to_analyze}
        for FVSstate, PBPA_given_FVSstate in FVSstate_PBPA_map.items():
            sum_of_PBPA += PBPA_given_FVSstate
            node_EAV_map_given_FVSstate = FVSstate_nodeEAVmap_map[FVSstate]
            for node in self.nodenames_to_analyze:
                EAV_given_FVSstate = node_EAV_map_given_FVSstate[node]
                node_EAV_map[node] += EAV_given_FVSstate*PBPA_given_FVSstate
        
        node_EAV_map = {node:EAV/sum_of_PBPA for node, EAV in node_EAV_map.items()}
        return node_EAV_map
            
            
    
    def _get_PBPA_given_FVS_state(self, FVS_state_map, node_EAV_map):
        """EAV is abbreviation of Ensemble Average Value

        Using the probability that each FVS sink node in the acyclic form has a state of 1 
        (recorded in node_EAV_map), 
        we calculate the probability of the FVS nodes having the state recorded in FVS_state_map
        (i.e. calculate PBPA=Probability of Being Point Attractor), 
        under the assumption that the probabilities of each FVS sink node being in state 1 are independent."""
        PBPA_given_FVS_state = 1
        for FVS_node, state in FVS_state_map.items():
            if state == 1:
                PBPA_given_FVS_state *= node_EAV_map[FVS_node]
            else:#state == 0
                PBPA_given_FVS_state *= 1 - node_EAV_map[FVS_node]

        return PBPA_given_FVS_state
    

class Block_of_acyclic_part(Block):
    def calculate_EAVs_of_nodes_and_NoPA_predicted(self, regulators_EAV_map:"{nodename: EAV}"):
        layers = self._get_layers_of_acyclic_form_given_FVS_and_regulators(self.nodenames_regulators)
        node_EAV_map = self._calculate_EAVs_given_layers(regulators_EAV_map, layers)
        
        return node_EAV_map, 1#predicted NoPA of acyclic part == 1. 
    
    def __repr__(self):
        return "Block of acyclic part {}".format(self.nodenames_to_analyze)