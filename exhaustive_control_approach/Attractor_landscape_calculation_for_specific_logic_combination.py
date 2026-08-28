import numpy as np

from Boolean_landscape_converge import Boolean_landscape_converge

class Logic_combination:
    def __init__(self, strctural_network_info, node_logic_map):
        self.node_names = strctural_network_info.node_names
        self.regulator_of_nodes = strctural_network_info.node_regulators_map
        self.node_logics = node_logic_map # value of this dict is a function that takes np.array as argument and returns 0 or 1.
    
    def make_next_state_function_with_perturbation(self, perturbation):
        """make function and return it.
        the function gets a network state as argument,
        and return next updated state."""
        perturbed_nodes = list(perturbation)
        perturbed_state = [perturbation[node] for node in perturbed_nodes]
        perturbed_state = np.array(perturbed_state, dtype=int)
        # print("perturbed state in logic combination obj", perturbed_state)
        
        node_names_new = [node_name for node_name in self.node_names if node_name not in perturbation]
        node_names_and_perturbed_nodes = node_names_new+perturbed_nodes
        regulator_indexes_of_nodes_perturbed = {}
        
        for node_name in node_names_new:
            regulators = self.regulator_of_nodes[node_name]
            regulator_indexes = [node_names_and_perturbed_nodes.index(regulator) for regulator in regulators]
            regulator_indexes_of_nodes_perturbed[node_name] = regulator_indexes
                
        def func_next_state(state_array_form):
            state_array_form_next = state_array_form.copy()
            state_array_form = np.concatenate((state_array_form, perturbed_state))
            
            for i, node_name in enumerate(node_names_new):
                regulator_indexes = regulator_indexes_of_nodes_perturbed[node_name]
                logic_func = self.node_logics[node_name]
                state_array_form_next[i] = logic_func(state_array_form[regulator_indexes])
                
            return state_array_form_next
        
        return node_names_new, func_next_state

    
    def calculate_landscape_given_perturbation(self, perturbation={}):
        """calculate attractor landscape for the given perturabtion"""
        num_of_nodes = len(self.node_names) - len(perturbation)
        landscape_calculator = Boolean_landscape_converge()
        landscape_calculator.num_of_nodes = num_of_nodes
        node_names_new, func_next_state = self.make_next_state_function_with_perturbation(perturbation)
        landscape_calculator.get_next_state = func_next_state
        if landscape_calculator.num_of_nodes > 12:
            landscape_calculator.converge_landscape(1000)
        else:
            landscape_calculator.calculate_landscape()
        
        return node_names_new, landscape_calculator