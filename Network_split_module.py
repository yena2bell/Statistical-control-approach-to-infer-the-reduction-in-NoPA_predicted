# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 12:03:53 2022

@author: jwKim
"""
import itertools

from SCC_decomposition_module import SCC_decomposition
from Blocks_module import Block_of_SCC, Block_of_acyclic_part
from Nodes_module import Node

class Network_structure_splited:
    def __init__(self, edges:"[(node from, sign, node to),,,]", find_minimum_FVSs=False):
        """If 'find_minimum_FVSs' is True, all minimum FVSs are calculated through exhaustive search. 
        If False, for SCCs with 15 nodes or fewer, minimum FVSs are found through exhaustive search, 
        while for larger SCCs, the SA FVSP NNS algorithm is used to calculate approximated minimum FVSs."""
        self.edges = self._check_edges(edges)
        
        self.input_nodes = [] #nodes with no incoming edges
        self.node_names = set()
        self.nodes_from_map = {} 
        #for node x, if there is an edge (node y, '+', node x), 
        #self.nodes_from_map[node x] contains node y
        self.nodes_to_map = {}
        #for node x, if there is an edge (node x, '+', node y), 
        #self.nodes_to_map[node x] contains node y
        self.nodename_object_map = {}
        self._parse_edges()
        
        self.Blocks_of_SCC = []
        self.Blocks_of_acyclic_part = []
        # A block is a concept defined to simplify calculations. 
        # When a network is divided into SCCs and the acyclic parts connecting them, 
        # each SCC and each acyclic part are defined as blocks, 
        # and the calculations are carried out based on these block units.
        self.find_minimum_FVSs= find_minimum_FVSs
        self._decompose_to_Blocks()
        
        # self.nodename_probof1_map = {}
    
    def _check_edges(self, edges):
        """Check the values of the edges. 
        There should only be one link between node_from X and node_to Y. 
        Additionally, ensure that the signs are unified as either '+' or '-'."""
        edges_wo_sign = set()
        edges_checked = []
        for edge in edges:
            edge_wo_sign = (edge[0], edge[-1])
            if edge_wo_sign not in edges_wo_sign:
                edges_wo_sign.add(edge_wo_sign)
            else:
                raise ValueError("there are more than two edges between {} and {}".format(edge_wo_sign[0], edge_wo_sign[1]))
            
            sign = edge[1]
            if sign in ('+', '1',1):
                sign = '+'
            elif sign in ('-', '-1',-1):
                sign = '-'
            else:
                raise ValueError("{} has inappropriate sign value!".format(edge))
            edge_new = (edge[0], sign, edge[-1])
            edges_checked.append(edge_new)
        
        return edges_checked
    
    def _parse_edges(self):
        """Find the source nodes (nodes with no incoming edges) from self.edges and store them in self.source_nodes. 
        Typically, when representing a network with edges, source nodes are often recorded with self-loops. 
        This should be taken into account. 
        Therefore, nodes with a self-positive loop and no other incoming edges are also treated as source nodes."""
        self_loop_sign_map = {}
        for edge in self.edges:
            self.node_names.add(edge[0])
            self.node_names.add(edge[-1])
        
        nodename_from_signs_map_map = {}
        
        for node_name in self.node_names:
            self.nodes_from_map[node_name] = set()
            self.nodes_to_map[node_name] = set()
            nodename_from_signs_map_map[node_name] = {}
            
        
        
        for edge in self.edges:
            node_to = edge[-1]
            node_from = edge[0]
            sign = edge[1]
            nodename_from_signs_map_map[node_to][node_from] = sign
            
            self.nodes_from_map[node_to].add(node_from)
            self.nodes_to_map[node_from].add(node_to)
            if node_from == node_to:
                self_loop_sign_map[node_from] = sign
        
        self.input_nodes = [node_name for node_name in self.node_names if not self.nodes_from_map[node_name]]
        
        for node_name in self.node_names:
            obj_node = Node(node_name)
            nodename_from_signs_map = nodename_from_signs_map_map[node_name]
            obj_node.set_regulators_signs(nodename_from_signs_map)
            obj_node.set_ensemble_average_function()                   
            self.nodename_object_map[node_name] = obj_node
        
        #filter source node which has self positive loop
        for node, sign in self_loop_sign_map.items():
            if len(self.nodes_from_map[node]) != 1:
                continue
            if sign == "+":
                self.input_nodes.append(node)
            else:
                print("{} node has self negative feedback and no in-coming edge.\nthis make model has no point attractor".format(node))
    
    def get_input_nodes(self):
        return self.input_nodes.copy()
    
    def set_specific_logic_to_node(self, node_name, regulators, logic_function):
        """If there is a node with known logic that you wish to utilize, 
        create a function that returns the value based on the given state according to the logic, 
        in the order of the regulators. 
        Then, place this function in the 'logic_function' slot.
        
        The logic to be provided should be a function that accepts a state vector 
        in the form of a numpy array composed of Boolean states (0 or 1) for the regulators and 
        returns the EAV (a real number between 0 and 1)."""
        obj_node= self.nodename_object_map[node_name]
        obj_node.change_regulator_order(regulators)
        obj_node.set_specific_Boolean_logic(logic_function)
    
    def _decompose_to_Blocks(self):
        """The network structure is divided into blocks"""
        SCCs_containing_feedback = self._decompose_to_SCC()
        nodes_in_SCCs = self._get_nodes_in_node_groups(SCCs_containing_feedback)
        nodes_in_acyclic_part = self.node_names.difference(nodes_in_SCCs)
        
        SCCindex_downstream_map = self._get_downstream_acycic_part_of_SCCs(SCCs_containing_feedback, nodes_in_SCCs)
        
        self.Blocks_of_SCC = self._get_objects_of_blocks_from_SCCs(SCCs_containing_feedback)
        self.Blocks_of_acyclic_part = self._get_objects_of_block_from_acyclic_part(nodes_in_acyclic_part, self.Blocks_of_SCC, SCCindex_downstream_map)
    
    def _decompose_to_SCC(self):
        """Decompose the network into SCCs.
        Select only the SCCs that contain feedback and return them.
        In this process, if an SCC consists of a single node, 
        it is likely to be a source node with a self-loop, which should be excluded."""
        SCCs = SCC_decomposition(self.edges)
        SCC_indexs_containing_feedback = []
        
        for i, SCC in enumerate(SCCs):
            if len(SCC) > 1:
                SCC_indexs_containing_feedback.append(i)
            else:#len(SCC)==1
                node_name = SCC[0]
                if node_name in self.input_nodes:
                    continue
                if self._node_have_selfloop(node_name):
                    SCC_indexs_containing_feedback.append(i)
        
        return [SCCs[i] for i in SCC_indexs_containing_feedback]
    
    def _node_have_selfloop(self, node_name):
        for edge in self.edges:
            if (edge[0] == node_name) and (edge[-1] == node_name):
                return True
        return False
    
    def _get_objects_of_blocks_from_SCCs(self, SCCs):
        """Create and return a blocks object 
        that contains information about each of the SCCs (Strongly Connected Components). 
        The returned list is ordered, 
        meaning that the block in the i-th position of the list corresponds to 
        the i-th SCC in the list of SCCs."""
        blocks_of_SCC = []
        for SCC in SCCs:
            block_of_SCC = self._get_object_of_block_from_SCC(SCC)
            blocks_of_SCC.append(block_of_SCC)
        return blocks_of_SCC
    
    def _get_object_of_block_from_SCC(self, SCC:list):
        """Receive the information about the nodes included in an SCC, 
        and use it to create an SCC Block object, 
        which is then returned."""
        regulators_of_SCC = self._regulators_of_nodes_group(SCC)
        block_SCC = Block_of_SCC(regulators_of_SCC, SCC, self.edges, self.nodename_object_map, 
                                 find_minimum_FVSs=self.find_minimum_FVSs)
        return block_SCC
        
    def _regulators_of_nodes_group(self, nodes_group):
        """For a given SCC, find and return any node X 
        that is a regulator of at least one of the nodes included in the SCC 
        but is not itself part of the SCC.
        The variable 'nodes_group' contains the nodes included in that SCC.
        
        The analysis will focus on SCCs that contain at least one feedback loop."""
        regulators_of_nodes_group = set()
        for node_name in nodes_group:
            regulators = self.nodes_from_map[node_name]
            regulators_of_nodes_group.update(regulators.difference(nodes_group))
        
        return regulators_of_nodes_group
    
    def _get_nodes_in_node_groups(self, node_groups):
        """if node_groups == [[node1, node2], [node3,node4]]
        then return set([node1, node2, node3, node4])"""
        nodes_in_nodegroups = set()
        for node_group in node_groups:
            nodes_in_nodegroups.update(node_group)
        
        return nodes_in_nodegroups
    
    def _get_downstream_acycic_part_of_SCCs(self, SCCs, nodes_in_SCCs):
        """For each SCC, find the nodes in the acyclic part that can be influenced by the SCC,
        meaning the nodes that exist downstream of the SCC.
        Return a map that uses the index of SCC in 'SCCs' list as the key and 
        its downstream nodes as the values."""
        SCCindex_downstream_map = {}
        for index_of_SCC, SCC in enumerate(SCCs):
            SCC_downstream = self._get_downstream_acycic_part_of_SCC(SCC, nodes_in_SCCs)
            SCCindex_downstream_map[index_of_SCC] = SCC_downstream
        
        return SCCindex_downstream_map

    def _get_downstream_acycic_part_of_SCC(self, SCC, nodes_in_SCCs):
        """For the given SCC, find the nodes in the acyclic part that can be influenced by the SCC, 
        meaning the nodes that exist downstream of the SCC.
        However, if the influence is only possible by passing through another SCC, 
        define those nodes as not being influenced."""
        nodes_downstream = set()
        stack = list(SCC)
        while stack:
            node = stack.pop()
            direct_downstream = self.nodes_to_map[node]
            direct_downstream.difference_update(nodes_in_SCCs)
            direct_downstream.difference_update(nodes_downstream)
        
            stack.extend(direct_downstream)
            nodes_downstream.update(direct_downstream)
        
        return nodes_downstream
    
    def _get_objects_of_block_from_acyclic_part(self, acyclic_part, 
                                               Blocks_of_SCC, 
                                               SCCindex_downstream_map):
        """A set of blocks containing parts of the acyclic part is created. 
        Even if the acyclic part is connected as a single entity, 
        it can be divided into multiple blocks
        depending on the relationship of each node with its SCC."""
        acyclic_part = set(acyclic_part)
        index_of_SCCs_not_yet_checked = set(range(len(Blocks_of_SCC)))
        blocks_of_acyclic_part = []
        nodes_checked = set()
        
        while acyclic_part:
            nodes_affected_by_SCCs = self._get_affected_nodes_by_SCCs(index_of_SCCs_not_yet_checked, Blocks_of_SCC, SCCindex_downstream_map)
            
            filtered_acyclic_part = acyclic_part.difference(nodes_affected_by_SCCs)

            block_of_acyclic_part = self._get_object_of_block_from_acyclic_part(filtered_acyclic_part)
            blocks_of_acyclic_part.append(block_of_acyclic_part)
            
            nodes_checked.update(filtered_acyclic_part)
            acyclic_part.difference_update(filtered_acyclic_part)
            
            while True:
                index_checked = self._get_SCC_satisfying_regulators(nodes_checked, Blocks_of_SCC, index_of_SCCs_not_yet_checked)
                if index_checked is None:
                    break
                else:
                    index_of_SCCs_not_yet_checked.remove(index_checked)
                    block_of_SCC = Blocks_of_SCC[index_checked]
                    nodes_checked.update(block_of_SCC.get_nodes_to_analyze())
        
        return blocks_of_acyclic_part

    def _get_affected_nodes_by_SCCs(self, index_of_SCCs, 
                                    Blocks_of_SCC, SCCindex_downstream_map):
        """Among all the SCCs, 
        select the SCCs located at the indices included in 'index_of_SCCs' from the 'Blocks_of_SCC' list. 
        Then, gather the nodes of those selected SCCs 
        and the nodes included in their downstream, and return them."""
        SCCs = [Blocks_of_SCC[index_of_SCC].get_nodes_to_analyze() for index_of_SCC in index_of_SCCs]
        nodes_in_SCCs = self._get_nodes_in_node_groups(SCCs)
        downstreams_of_SCCs = [SCCindex_downstream_map[index_of_SCC] for index_of_SCC in index_of_SCCs]
        nodes_in_downstreams = self._get_nodes_in_node_groups(downstreams_of_SCCs)
        
        return nodes_in_SCCs.union(nodes_in_downstreams)
    
    def _get_object_of_block_from_acyclic_part(self, acyclic_part):
        """Create a block object using the given acyclic part and return it."""
        regulators_of_acyclic_part = self._regulators_of_nodes_group(acyclic_part)
        acyclic_part_not_input_nodes = []
        for node in acyclic_part:
            if node in self.input_nodes:
                regulators_of_acyclic_part.add(node)
            else:
                acyclic_part_not_input_nodes.append(node)
        block_acyclic = Block_of_acyclic_part(regulators_of_acyclic_part, 
                                              acyclic_part_not_input_nodes, 
                                              self.edges, 
                                              self.nodename_object_map)
        return block_acyclic
    
    def _get_SCC_satisfying_regulators(self, nodes_checked, blocks_of_SCCs, index_not_yet_checked):
        """For every index i in 'index_not_yet_checked', 
        check whether all regulators of the SCC corresponding to blocksofSCCs[i] are included in 'nodes_checked'. 
        Return the first index i that satisfies this condition. 
        If no such index is found, return None."""
        for index in index_not_yet_checked:
            block_of_SCC = blocks_of_SCCs[index]
            if nodes_checked.issuperset(block_of_SCC.get_regulator_nodes()):
                return index
        else:
            return None
    
    def _apply_control_to_nodes(self, control={}):
        """Applies the control state to the node object.
        and return the controlled node objects as a list"""
        nodes_controlled = []
        for node, state in control.items():
            node_obj = self.nodename_object_map[node]
            node_obj.is_controlled_to(state)
            nodes_controlled.append(node_obj)
        
        return nodes_controlled
    
    def _reset_control(self, controlled_nodes_obj):
        """Restores the controlled node objects in 'controlled_nodes_obj' 
        to their original uncontrolled node objectes"""
        for node_obj in controlled_nodes_obj:
            node_obj.reset_control()
        
    def calculate_NoPA_prediction_given_input_condition(self, input_condition={}, control={}, return_eas=False):
        """It calculates and returns the NoPA_predicted value 
        for a given 'input_condition' == {input node: state}. 
        For input nodes not specified in 'input_condition', 
        it calculates and sums the cases where the input node is both on and off. 
        
        EAV is abbreviation of Ensemble Average Value

        If 'return_eas'=True, 
        it also returns the probability of 1 calculated for each node during this process."""
        controlled_node_objs = self._apply_control_to_nodes(control)
            
        NoPA_predicted = 0
        input_nodes_not_determined = [input_node for input_node in self.input_nodes if input_node not in input_condition]
        for input_state_not_determined in itertools.product((0,1), repeat=len(input_nodes_not_determined)):
            NoPA_predicted_given_input_condition = 1
            
            node_EAV_map = {input_nodes_not_determined[i]:state for i, state in enumerate(input_state_not_determined)}
            node_EAV_map = {**node_EAV_map, **input_condition}
            # For all nodes, the EAV is calculated and stored in this variable, 
            # but it is initially computed and stored for the input nodes first.
            
            blocks = self.Blocks_of_SCC + self.Blocks_of_acyclic_part
            while blocks:
                for i, block in enumerate(blocks):
                    regulators_of_block = set(block.get_regulator_nodes())
                    if regulators_of_block.issubset(node_EAV_map):
                        # Select any block that satisfies this condition and proceed.
                        blocks.pop(i)
                        regulator_EAV_map = {regulator:node_EAV_map[regulator] for regulator in regulators_of_block}
                        blocknode_EAV_map, NoPA_block_predicted = block.calculate_EAVs_of_nodes_and_NoPA_predicted(regulator_EAV_map)
                        #if the block is acyclic part, 'NoPA_predicted' of that block becomes 1
                        node_EAV_map = {**node_EAV_map, **blocknode_EAV_map}
                        NoPA_predicted_given_input_condition *= NoPA_block_predicted
                        # print(NoPA_block_predicted, NoPA_predicted_given_input_condition)
                        # In a single input condition, 
                        # multiply the NoPA_predicted of each block to obtain the NoPA_predicted 
                        # for that input condition.
                        break#for
                else:
                    # At least one block must have all of its regulators with the probability of 1 already calculated.
                    raise ValueError("no blocks are not ready")

            NoPA_predicted += NoPA_predicted_given_input_condition
        
        self._reset_control(controlled_node_objs)
        if return_eas:
            return NoPA_predicted, node_EAV_map
        else:
            return NoPA_predicted