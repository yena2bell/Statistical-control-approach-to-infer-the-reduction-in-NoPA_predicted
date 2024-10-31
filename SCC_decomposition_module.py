# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 12:18:01 2022

@author: jwKim

This module contains functions related to decomposing a directed network structure into strongly connected components (SCCs).
"""

def SCC_decomposition(links):
    """
    This function takes a network structure given in the form of links, decomposes it into SCCs, and returns groups of nodes that belong to each SCC.

    links = [(node1, ,,,node2), (node1,,,, node3)...]
    (node1,,,, node2) means node1 interacte to node2 i.e. node1 -> node2

    SCCs = [[node_1 in SCC_1, node_2 in SCC_1,,, node_i in SCC_1], [node_1 in SCC_2, node_2 in SCC_2...]]
    """
    remained_links = list(links)
    #print("the number of links to analyze is", len(lRemained_links))
    #copy the list data to conserve original data

    remained_nodes = set()
    for link in remained_links:
        remained_nodes.add(link[0])
        remained_nodes.add(link[-1])
    #print("the number of nodes to analyze is", len(lRemained_nodes))
    SCCs = []

    while(remained_nodes):
        start_node = remained_nodes.pop()
        SCCs += _find_SCC_under_startnode(start_node, remained_nodes, remained_links)
        """
        choose one node and make it start node.
        find SCC containing that start node and SCC whose hierarchy is lower than SCC containing start node
        repeat until find all SCCs
        """

    return SCCs


def _find_SCC_under_startnode(start_node, remained_nodes, remained_links):
    """
    sub function of 'SCC_decomposition'
    remained_nodes = [node name1, node name2, ..... node name k]
    remained_links = [(node1,,,, node2), (node1,,,, node3)...]
    (node1,,,, node2) means node1 interacte to node2 i.e. node1 -> node2
    remained nodes set don't contain start node
    """

    flow_of_nodes = [start_node]
    set_of_SCCs = []
    cycle_positions = []
    
    link_indexes_to_delete = []
    
    while flow_of_nodes:
        remained_links = [link for i, link in enumerate(remained_links) if i not in link_indexes_to_delete]
        link_indexes_to_delete = []
        
        for link_index, link in enumerate(remained_links):
            node_from = link[0]
            node_to = link[-1]
            if node_from == start_node:
                next_node = node_to
                link_indexes_to_delete.append(link_index)
                
                if next_node in flow_of_nodes:
                    cycle = (flow_of_nodes.index(next_node),len(flow_of_nodes)-1)
                    cycle_positions = _evaluate_SCC_inclusion(cycle_positions, cycle) 
                    break 
                elif next_node in remained_nodes:
                    flow_of_nodes.append(next_node)
                    remained_nodes.remove(next_node)
                    break                
        else:
            position_of_startnode = flow_of_nodes.index(start_node)
            if not(cycle_positions):
                set_of_SCCs.append([flow_of_nodes.pop(-1)])
                #single node SCC without self loop
            elif position_of_startnode >cycle_positions[-1][1]:
                set_of_SCCs.append([flow_of_nodes.pop(-1)])
                #single node SCC without self loop
            elif position_of_startnode == cycle_positions[-1][0]:      
                SCC = cycle_positions.pop(-1)
                set_of_SCCs.append(flow_of_nodes[SCC[0]:SCC[1]+1])
                flow_of_nodes = flow_of_nodes[:SCC[0]]
                
            if flow_of_nodes:
                start_node = flow_of_nodes[position_of_startnode-1]
            continue#go to start of while
        
        start_node = flow_of_nodes[-1] 
       
    return set_of_SCCs


def _evaluate_SCC_inclusion(SCCs_cycle_form, new_SCC_cycle_form):
    """
    sub function of '_find_SCC_under_startnode'

    'SCCs_cycle_form' contain information about node groups confirmed to be in the same SCC within flow_of_nodes. 
    Each 'SCC_cycle_form' is represented as a tuple in the form of (a, b), where a and b are integers such that a < b, 
    and they represent indices in flow_of_nodes. This means that the nodes from flow_of_nodes[a:b+1] belong to the same SCC.

    'SCCs_cycle_form' take the form of a list of tuples [(a, b), (c, d), ...] 
    where the indices satisfy a < b < c < d. Example: SCCs_cycle_form = [(3, 8), (11, 20), ...]

    'new_SCC_cycle_form' represents newly discovered cycle information in flow_of_nodes. 
    When new_SCC is (x, y), the value of y satisfies b <= y for any existing SCC=(a, b) in SCCs. 
    If there is an overlap with an existing SCC, the two are merged into one.
    """

    for SCC_cycle_form in SCCs_cycle_form:
        if SCC_cycle_form[1] < new_SCC_cycle_form[0]:
            continue #tCycle has no common nodes with tNewCycle. so go to next cycle
        else:
            position_of_SCC = SCCs_cycle_form.index(SCC_cycle_form)
            if SCC_cycle_form[0] <= new_SCC_cycle_form[0]:#cycle[1] >= new_cycle[0]
                new_SCC_cycle_form = (SCC_cycle_form[0],new_SCC_cycle_form[1])
            #else: cycle[1] >= new_cycle[0] and cycle[0]>new_cycle[0]
            break
    else:
        #new cycle is not intersected to any of cycle in cycles
        SCCs_cycle_form.append(new_SCC_cycle_form)
        return SCCs_cycle_form

    SCCs_cycle_form = SCCs_cycle_form[0:position_of_SCC]
    SCCs_cycle_form.append(new_SCC_cycle_form)
    return SCCs_cycle_form


def net_of_SCCs(SCCs, links):
    """
    SCCs = [[node1,node2,node3... nodes in the SCC1],[node6,node7.... nodes in the SCC2],....]
    links = [(node1,,, node2), (node1,,,, node3)...]
    
    calculate links between SCCs.
    When there are two SCCs, A and B, if there is at least one link from any node a in SCC A to any node b in SCC B (node a --> node b), 
    it is considered that a link exists between SCC A and SCC B (SCC A --> SCC B). 
    These links are collected and returned.
    
    returned value is the list [(SCC1's number,SCC2's number),...] 
    this means that link connecting SCC1 -> SCC2 exists
    """
    links = list(links)
    links_connecting_SCCs = set()
    
    for index_SCC, SCC in enumerate(SCCs):
        for i_link in range(len(links)-1,-1,-1):
            link = links.pop(i_link)
            if link[0] in SCC:
                if link[-1] not in SCC:
                    index_SCC_connected = _node_position_finding(SCCs, link[-1])
                    link_connecting_SCCs = (index_SCC,index_SCC_connected)
                    links_connecting_SCCs.add(link_connecting_SCCs)

            elif link[-1] in SCC:
                index_SCC_connected = _node_position_finding(SCCs, link[0])
                link_connecting_SCCs = (index_SCC_connected, index_SCC)
                links_connecting_SCCs.add(link_connecting_SCCs)

    links_connecting_SCCs =list(links_connecting_SCCs)

    return links_connecting_SCCs


def _node_position_finding(SCCs, node_name):
    """
    sub function of 'net_of_SCCs'
    SCCs = [[node1,node2,node3... nodes in the SCC1],[node6,node7.... nodes in the SCC2],....]
    find SCC index containg node_name
    """
    for i, SCC in enumerate(SCCs):
        if node_name in SCC:
            return i
    else:
        raise(ValueError("{} is not contained any SCCs.".format(node_name)))