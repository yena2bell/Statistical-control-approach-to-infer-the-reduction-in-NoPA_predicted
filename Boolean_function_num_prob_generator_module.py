# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 15:40:26 2022

@author: jwKim
"""
import operator as op
from functools import reduce

def get_prob_of_1_for_nested_canalzing_functions(state_of_regulators:"(1,0,0,0)"):
    """
    assume that There are n regulators, and all of these regulators act as activations.
    We can consider all possible nested canalizing functions that satisfy the above condition.
    
    Assuming that all nested canalizing functions have an equal probability of being chosen, 
    this function returns the average output for a specific regulator state composed of n Boolean states, 
    based on each of the nested canalizing functions."""
    num_of_regulators = len(state_of_regulators)
    num_of_1s = sum(state_of_regulators)
    return _num_of_nested_canalizing_function_given_1s_and_num_of_regulators(num_of_regulators, num_of_1s)/num_of_nested_canalizing_function_with_(num_of_regulators)

def comb(n, r):
    """In Python 3.8 or later, it can be replaced with math.comb"""
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n-r, -1), 1)
    denom = reduce(op.mul, range(1, r+1), 1)
    return numer // denom

def memorize_and_return(func):
    """Decorator function. For a specific function, 
    if the input value has been previously calculated, 
    it allows the result from that time to be retrieved immediately."""
    argument_result_map = {}
    def memorized_func(*args):
        if args in argument_result_map:
            return argument_result_map[args]
        else:
            value = func(*args)
            argument_result_map[args] = value
            return value
    
    return memorized_func
        
@memorize_and_return
def num_of_nested_canalizing_function_with_(num_of_regulators):
    """assume that There are n regulators, and all of these regulators act as activations.
    This function returns the total number of nested canalizing functions that satisfy the above conditions."""
    if num_of_regulators == 0:
        return 1
    elif num_of_regulators == 1:
        return 1
    else:
        num_of_nested_canalizing_function = 0
        for i in range(1, num_of_regulators+1):
            num_of_nested_canalizing_function += pow(-1, i+1) * comb(num_of_regulators, i) * 2 * num_of_nested_canalizing_function_with_(num_of_regulators - i)
        return num_of_nested_canalizing_function
    

def num_of_nested_canalizing_function_with_regulator_state(state_of_regulators:"(1,0,0,0)"):
    """assume that There are n regulators, and all of these regulators act as activations.
    This function returns the number of nested canalizing functions, 
    among those that satisfy the above conditions, 
    which produce an output of 1 when given the specified regulator state (state_of_regulators) as input."""
    num_of_regulators = len(state_of_regulators)
    num_of_1s = sum(state_of_regulators)
    return _num_of_nested_canalizing_function_given_1s_and_num_of_regulators(num_of_regulators, num_of_1s)

@memorize_and_return
def _num_of_nested_canalizing_function_given_1s_and_num_of_regulators(num_of_regulators, num_of_1s):
    """assume that There are n regulators, and all of these regulators act as activations.

    This function counts the number of nested canalizing functions that satisfy the above condition, 
    specifically those where the input regulator state has the first 'num_of_1s' regulators set to 1 
    and the remaining ones set to 0 (for example: (1, 1, 1, 0, 0) when num_of_1s=2), 
    and for which the output is 1."""
    if num_of_1s == 0:
        return 0
    elif num_of_regulators == num_of_1s:
        return num_of_nested_canalizing_function_with_(num_of_regulators)
    else:
        num_of_functions_answer = 0
        for num_of_canalizing_factors in range(1, num_of_regulators+1):
            num_of_except = num_of_regulators - num_of_canalizing_factors
            num_of_functions_with_the_num_of_canalizing_factors = 0
            num_comb_included_in_1s = 0
            num_comb_included_in_0s = 0
            if num_of_canalizing_factors <= num_of_1s:
                num_comb_included_in_1s = comb(num_of_1s, num_of_canalizing_factors)
                num_of_functions_with_the_num_of_canalizing_factors += num_comb_included_in_1s * num_of_nested_canalizing_function_with_(num_of_except)
                
                num_of_functions_with_the_num_of_canalizing_factors += num_comb_included_in_1s * _num_of_nested_canalizing_function_given_1s_and_num_of_regulators(num_of_except, num_of_1s-num_of_canalizing_factors)
            if num_of_canalizing_factors <= num_of_regulators - num_of_1s:
                num_comb_included_in_0s = comb(num_of_regulators - num_of_1s, num_of_canalizing_factors)
                num_of_functions_with_the_num_of_canalizing_factors += num_comb_included_in_0s * _num_of_nested_canalizing_function_given_1s_and_num_of_regulators(num_of_except, num_of_1s)
            
            num_comb_include_both_1_and_0 = comb(num_of_regulators, num_of_canalizing_factors) - num_comb_included_in_1s - num_comb_included_in_0s
            num_of_functions_with_the_num_of_canalizing_factors += num_comb_include_both_1_and_0 * num_of_nested_canalizing_function_with_(num_of_except)
            
            num_of_functions_answer += pow(-1, num_of_canalizing_factors+1)*num_of_functions_with_the_num_of_canalizing_factors
        
        return num_of_functions_answer