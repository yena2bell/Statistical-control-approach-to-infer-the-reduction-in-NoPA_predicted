# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 10:36:39 2022

@author: jwKim

"""
import numpy as np
import random

class Boolean_landscape_converge:
    def __init__(self):
        self.num_of_nodes = None
        self.get_next_state = None
        
        self.att_basin_ratio = {}
        self.att_basin_intform = {}
        self.intform_states_calculated = set()
        
        self.ratio_diff_threshold = 0.01
        self.unchanged_continuation = 100
    
    def _int2state(self, int_st):
        """ Convert integer to state
        """
        fstr = "{0:0%db}" % (self.num_of_nodes)
        str_st = fstr.format(int_st)
        # print("state in int2state", np.array(list(str_st), dtype=int))
        return np.array(list(str_st), dtype=int)

    def _state2int(self, st):
        """Convert state to integer.
        """
        str_st = ''.join([str(int(x)) for x in st])
        return int(str_st, 2)
    
    def _calculate_basin_ratio(self, att_basin_intform):
        """`att_basin_intform` is {att: set of basin states} form. 
        this is converted to the form of {att:basin ratio}"""
        num_all_states = len(self.intform_states_calculated)
        return {att:len(basin)/num_all_states for att, basin in att_basin_intform.items()}
    
    def _new_ratio_is_different(self, att_basin_ratio_new):
        """compare `self.att_basin_ratio` and `att_basin_ratio_new`. 
        if these are different enough (over the threshold), return True.
        
        `att_basin_ratio_new` is assumed to be `self.att_basin_ratio` with additional information"""
        for att, basin_ratio_new in att_basin_ratio_new.items():
            basin_ratio_old = self.att_basin_ratio.get(att, 100)
            if abs(basin_ratio_old - basin_ratio_new) >= self.ratio_diff_threshold:
                return True
        else:
            return False
    
    def converge_landscape(self, minimum_simulation=None):
        """continue simulation until `attractor basin ratio` is converged.
        if converged, quit this method.
        `minimum_simulation` simulation is done regardless convergence."""
        if minimum_simulation is None:
            minimum_simulation = 2000
        state_all_1 = pow(2, self.num_of_nodes) -1
        unchanged_continuation = self.unchanged_continuation
        interval_simuls = minimum_simulation
        while len(self.intform_states_calculated) <= state_all_1:
            state_intform = random.randint(0, state_all_1)
            if state_intform in self.intform_states_calculated:
                continue
            else:
                interval_simuls -= 1
                self._follow_trajectory(state_intform)
                if interval_simuls > 0:
                    continue
                #print("middle check", len(self.intform_states_calculated))
                att_basin_ratio_new = self._calculate_basin_ratio(self.att_basin_intform)
                if not self._new_ratio_is_different(att_basin_ratio_new):
                    self.att_basin_ratio = att_basin_ratio_new
                    unchanged_continuation -= 1
                    interval_simuls = minimum_simulation
                    #print(unchanged_continuation, len(self.intform_states_calculated))
                    if unchanged_continuation == 0:
                        print("{}/{} are tested".format(len(self.intform_states_calculated),state_all_1+1))
                        break# no change of basin ratio -> assume convergence occurs
                else:
                    #print(len(self.intform_states_calculated),'/',state_all_1, "calculation, landscape inferenced changed")
                    unchanged_continuation = self.unchanged_continuation
                    interval_simuls = minimum_simulation
                    # initialize
                    self.att_basin_ratio = att_basin_ratio_new
        else:
            #(len(self.intform_states_calculated) == state_all_1 + 1)
            print("all possible states",len(self.intform_states_calculated)," are tested")
            self.att_basin_ratio = self._calculate_basin_ratio(self.att_basin_intform)

    
    def calculate_landscape(self):
        """calculate attractor basin landscape using all states."""
        if self.num_of_nodes == 0:
            return
        for state_intform in range(pow(2, self.num_of_nodes)):
            if state_intform in self.intform_states_calculated:
                continue
            else:
                self._follow_trajectory(state_intform)
                
        self.att_basin_ratio = self._calculate_basin_ratio(self.att_basin_intform)
    
    def get_state_ratio_tested(self):
        """return states ratio used to converge the landscape."""
        return len(self.intform_states_calculated)/pow(2,self.num_of_nodes)
    
    def _follow_trajectory(self, state_intform):
        trajectory = [state_intform]
        array_state = self._int2state(state_intform)
        while True:
            array_state = self.get_next_state(array_state)
            state_intform = self._state2int(array_state)
            if state_intform in self.intform_states_calculated:
                # it reaches to previous attractor or basin
                self.intform_states_calculated.update(trajectory)
                for basin_intforms in self.att_basin_intform.values():
                    if state_intform in basin_intforms:
                        basin_intforms.update(trajectory)
                        break#for
                break
            elif state_intform in trajectory:#new attractor!
                self.intform_states_calculated.update(trajectory)
                new_basin = set(trajectory)
                new_att = self._arrange_attractor_states(trajectory[trajectory.index(state_intform):])
                self.att_basin_intform[new_att] = new_basin
                break
            else:
                trajectory.append(state_intform)
    
    def _arrange_attractor_states(self, state_intforms:list):
        """convert format of attractor from list to tuple form.
        order of network state is arranged."""
        state_min = min(state_intforms)
        return tuple(state_intforms[state_intforms.index(state_min):]+state_intforms[:state_intforms.index(state_min)])
                
        