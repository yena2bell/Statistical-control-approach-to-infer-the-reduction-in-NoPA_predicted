# -*- coding: utf-8 -*-
"""
Created on Sat Feb 27 16:40:03 2021

@author: jwKim
"""

def get_line_num_of_regulator_states_in_truthtable(t_b_regulators):
    return sum((pow(2,i)*state for i,state in enumerate(t_b_regulators)))

def Boolean_function(i_logic, t_b_inputs):
    """
    t_b_inputs = (True, False, False, True, false)
            ->(1,0,0,1,0)
            -> 1+2*0+4*0+8*1+16*0 = 9
    then this input needs 9+1th line of logic table

    output value in ith line of logic table is
    ith value of binary number of iLogic number
    if iLogic is 25 then binary number is 11001
    then 4th line output is 1 and 3th line output is 0

    element1 element2 element3 output
    0        0        0        a0
    1        0        0        a1
    0        1        0        a2
    1        1        0        a3
    0        0        1        a4
    1        0        1        a5
    0        1        1        a6
    1        1        1        a7

    (1,0,1) has output value in (1+4)+1th line
    i_logic is sum of ai*(2^i)
    
    if t_b_inputs == [],  Boolean_function(0,[]) == False,  Boolean_function(1,[]) == True. 
    """
    
    #check the range of iLogic
    if (pow(2, pow(2,len(t_b_inputs))) <= i_logic) or (i_logic < 0):
        print("logic number range error")
        return

    iLine_position = get_line_num_of_regulator_states_in_truthtable(t_b_inputs)

    iLine_output = (i_logic >> iLine_position)%2

    if iLine_output == 1:
        return(True)
    else:
        return(False)
        
def output_logictable_of_i_logic(i_logic,i_numofinputs, ts_inputnodes=None):
    """
    output the Boolean logic table of the given i_logic.
    Boolean table is returned by string form.
    output is the string such as
    element1 element2 element3 output
    0        0        0        a0
    1        0        0        a1
    0        1        0        a2
    1        1        0        a3
    0        0        1        a4
    1        0        1        a5
    0        1        1        a6
    1        1        1        a7
    if ts_inputnodes == None, first line shows element1 element2 ....
    if ts_inputnodes == (s_inputnode1, s_inputnode2 ....), first line show these names
    """
    s_table = ''
    if ts_inputnodes:
        for s_inputnode in ts_inputnodes:
            s_table += s_inputnode+'\t'
        s_table += "output\n"
    else:
        for i in range(i_numofinputs):
            s_table += "element{}\t".format(i+1)
        s_table += "output\n"
    
    for i in range(pow(2,i_numofinputs)):
        state = []
        for _ in range(i_numofinputs):
            s_table += "{}\t".format(i%2)
            state.append(i%2)
            i = i >> 1
        s_table += "{}\n".format(Boolean_function(i_logic, state))
    
    return s_table