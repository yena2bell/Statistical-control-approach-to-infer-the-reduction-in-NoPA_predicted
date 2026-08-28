# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 13:56:39 2022

@author: jwKim
"""
import sys, os, itertools

import Boolean_truthtable_calculation as BTC

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Boolean_function_num_prob_generator_module as BFG


def get_nested_canalizing_functions_with_regulators_num_of(num_of_regulators):
    """make all possible nested canalizing functions 
    that node with `num_of_regulators' number of regulators
    can have, and return them in a list."""

    nc_logics = set()
    regulator_indexes = list(range(num_of_regulators))

    for canalizing_order in itertools.permutations(regulator_indexes):
        for canalizing_values in itertools.product((0,1), repeat=num_of_regulators):
            logic_truthtable_integer = get_nested_canalizing_function_with_canalinzing_order_and_values(canalizing_order, canalizing_values)
            nc_logics.add(logic_truthtable_integer)
            
    #check
    num_of_logics = BFG.num_of_nested_canalizing_function_with_(num_of_regulators)
    if len(nc_logics) != num_of_logics:
        print("the num of nested canalizing function should be {}, but calculated nested-canalizing function is {}!".format(num_of_logics, len(nc_logics)))
        
    return nc_logics

def get_nested_canalizing_function_with_canalinzing_order_and_values(canalizing_order, canalizing_values):
    """assume that There are ordered n regulators, 
    and there canalization power is ordered as `canalizing_order`, 
    and the canalizing values are `canalizing_values`.
    
    calculate truthtable satisfying the above conditions, 
    and return the truthtable as an integer."""
    num_of_regulators = len(canalizing_order)
    nc_logic_truthtable_integer = 0

    for regulator_state in itertools.product((0,1), repeat=num_of_regulators):
        canalizing_node_affecting = _regulator_state_check(regulator_state, canalizing_order, canalizing_values)
        if regulator_state[canalizing_node_affecting] == 1:
            line_in_truthtable = BTC.get_line_num_of_regulator_states_in_truthtable(regulator_state)
            nc_logic_truthtable_integer += pow(2, line_in_truthtable)
    
    return nc_logic_truthtable_integer

def _regulator_state_check(regulator_state, canalizing_order, canalizing_values):
    """find canalizing node that dominates the given regulator state."""
    for i, regulator_index in enumerate(canalizing_order):
        if regulator_state[regulator_index] == canalizing_values[i]:
            return regulator_index
    else:
        return canalizing_order[-1]