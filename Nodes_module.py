# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 15:44:55 2022

@author: jwKim
"""
import numpy as np
import itertools
import Boolean_function_num_prob_generator_module as BFNPG

class Node:
    def __init__(self, node_name):
        self.node_name = node_name
        self._regulators = () 
        #when this node is 'node to' for some edges, 'node from's are regulator of this node
        self._signs = ()#'+' or '-'
        
        self.Boolean_probability_function = None
        self.Boolean_probability_function_save = None
        self._num_of_possible_logics = 1
    
    def __repr__(self):
        return self.node_name
    
    def set_regulators_signs(self, regulator_signs_map):
        """regulator_modalities_map = {regulator1: modality of the regulator,,,} """
        regulators = []
        signs = []
        for regulator, sign in regulator_signs_map.items():
            regulators.append(regulator)
            signs.append(sign)
        self._regulators = tuple(regulators)
        self._signs = tuple(signs)
        
    def is_controlled_to(self, controlled_state):
        """Make the node controlled to the 'controlled_state'. 
        To do this, replace the logic with one that only returns the controlled_state value. 
        The original logic is saved in self.Boolean_probability_function_save."""
        self.Boolean_probability_function_save = self.Boolean_probability_function
        
        def controlled_logic(array_state):
            """always return 'controlled_state' value"""
            return controlled_state
        
        self.Boolean_probability_function = controlled_logic
    
    def reset_control(self):
        """Return the controlled node to the uncontrolled node."""
        self.Boolean_probability_function = self.Boolean_probability_function_save
        self.Boolean_probability_function_save = None
        
        
    def change_regulator_order(self, regulator_order):
        """Change the order of self._regulators recorded as a tuple to regulator_order.
        During this process, also adjust self._signs
        
        After executing this method, self.Boolean_probability_function must be reconfigured."""
        if set(self._regulators) != set(regulator_order):
            raise ValueError("newly entered regulators {} are differnt to old regulators {}".format(set(regulator_order), set(self._regulators)))
        
        signs_new = []
        for regulator in regulator_order:
            index_of_regulator = self._regulators.index(regulator)
            signs_new.append(self._signs[index_of_regulator])
        
        self._regulators = tuple(regulator_order)
        self._signs = tuple(signs_new)
    
    def get_EAV_given_regulator_EAVs(self, regulator_EAVs:"list or tuple form probabilities"):
        EAV_result = 0
        for regulator_state in itertools.product((False,True), repeat=len(self._regulators)):
            array_state = np.array(regulator_state)
            prob_of_state = self._get_prob_of_state_assuming_independent(array_state, regulator_EAVs)
            EAV_result_of_state = self.Boolean_probability_function(array_state)
            # Calculates the 'probability of 1' for a regulated node when its regulators have specific Boolean values.

            #print(regulator_state, prob_of_state, prob_result_of_state)
            EAV_result += EAV_result_of_state * prob_of_state
        return EAV_result
    
    def _get_prob_of_state_assuming_independent(self, array_state, regulator_probs):
        """For a node X with regulators R1 and R2, 
        where the 'probability of 1' for each regulator is p1 and p2 respectively:

        The probability of R1=1 and R2=1 is calculated as p1*p2.
        The probability of R1=1 and R2=0 is calculated as p1*(1-p2).
        The probability of R1=0 and R2=1 is calculated as (1-p1)*p2.
        The probability of R1=0 and R2=0 is calculated as (1-p1)*(1-p2).
        
        this method returns the probability of given regulator state ('array_state')"""
        prob_of_state = 1
        for i, state in enumerate(array_state):
            if state:#state == 1 or True
                prob_of_state *= regulator_probs[i]
            else:
                prob_of_state *= (1 - regulator_probs[i])
        return prob_of_state
    
    @property
    def regulators(self):
        return self._regulators
    
    def set_ensemble_average_function(self):
        """For each node, an ensemble average function is assigned. 
        The ensemble average function calculates the ensemble average value (EAV) 
        by considering all possible nested canalizing logics 
        that meet the three constraints outlined in the paper. 
        
        Simply put, the ensemble average value represents the probability 
        that the node’s state will be 1 
        when all possible nested canalizing functions are considered."""
        index_of_inhibiting_regulators = []
        for index, sign in enumerate(self._signs):
            if sign == '-':
                index_of_inhibiting_regulators.append(index)
        def ensemble_average_function(regulators_state:"numpy.array"):
            regulators_state[index_of_inhibiting_regulators] = np.abs(1-regulators_state[index_of_inhibiting_regulators])
            return BFNPG.get_prob_of_1_for_nested_canalzing_functions(regulators_state)
        
        self.set_specific_Boolean_logic(ensemble_average_function)
        self._num_of_possible_logics = BFNPG.num_of_nested_canalizing_function_with_(len(self._regulators))
    
    def set_specific_Boolean_logic(self, func):
        self._num_of_possible_logics = 1
        self.Boolean_probability_function = func