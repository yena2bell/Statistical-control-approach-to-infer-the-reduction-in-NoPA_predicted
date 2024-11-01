# Statistical control approach

This program is based on the following paper:
> Kim, Jongwan, Corbin Hopper, and Kwang-Hyun Cho. "Statistical control of structural networks with limited interventions to minimize cellular phenotypic diversity represented by point attractors." Scientific Reports 13.1 (2023): 6275.

which is freely available here: https://www.nature.com/articles/s41598-023-33346-1

This program calculates the reduction in NoPA_predicted when a structural network model and control are provided, compared to when there is no control. 
The structural network model represents a network model comprising nodes and signed edges (activating or inhibiting) that convey network structure. 
Control involves setting some of the nodes in the structural network model as control targets and fixing the state of each control node to 1 (Over-expression) or 0 (Knocked-out).

NoPA is short for the number of point attractors. When Boolean logic is assigned to the structural network model, NoPA_true represents the number of point attractors for the Boolean network model. 
NoPA_predicted is an estimated value of NoPA_true, assuming no prior information about the Boolean logic.
The reduction in NoPA_predicted is the value obtained by subtracting the NoPA_predicted under control from the NoPA_predicted when no control is applied. (i.e. 'reduction in NoPA_predicted' = 'NoPA_predicted with no control' - 'NoPA_predicted with control')

# Installation
Download this GitHub repository to use the program.


# Requirements
- NumPy (v1.25.0+) https://numpy.org/

  - Note: Older versions are also expected to work.

# Features
- Reads a network structure file formatted as TSV.
- Calculates the reduction of NoPA_predicted for each input condition as well as the overall reduction with a given control.
- Allows for choosing between a brute-force search to find the minimum FVS or an approximate minimum FVS calculation.
- If Boolean logic for a specific gene is known, it can be applied to the corresponding node to improve the prediction accuracy of NoPA_predicted. Not yet implemented.

# Basic usage example
Run main.py from the downloaded folder.

```python main.py <source of structural network file> --control "node1 = s1, node2 = s2" [--find_minimum_FVSs <True|False>]```

Here, ```<source of structural network file>``` is the address of a file in TSV format containing signed edge information of the structural network to estimate NoPA_predicted. See example files in the example_structural_networks folder for format reference.

```--control``` is a required option specifying the control to apply. When controlling two targets, node1 and node2, and fixing each node's state to s1 and s2, provide the input "node1=s1, node2=s2" after ```--control```. The state for each node should be either 1 or 0.

```--find_minimum_FVSs``` is an option directing the algorithm to use brute-force search to find the minimum FVS.
- If ```--find_minimum_FVSs True```, the algorithm will use brute-force search to find the minimum FVS. For large networks, this may increase computational complexity.
- If ```--find_minimum_FVSs False```, the algorithm searches for the minimum FVS only in small SCCs (15 or fewer nodes) and uses the SA-FVSP-NNS algorithm to find an approximate minimum FVS in larger SCCs.

The default is --find_minimum_FVSs False.

For the example network model provided, applying control to fix the GATA3 node to 1 in the T cell differentiation model would use the following command:
```python main.py "./example_structural_networks/T cell differentiation.tsv" --control "GATA3 = 1"```
The output will be:
```
the file to read the network structure is  ./example_structural_networks/T cell differentiation.tsv
control to apply the structural network is  {'GATA3': 1}
this algorithm will find approximated minimum FVSs
reduction of NoPA_predicted by control {'GATA3': 1} in input condition {'IL12': 0, 'IFNb': 0, 'IL18': 0, 'TCR': 0} is
0.7473457060664535
reduction of NoPA_predicted by control {'GATA3': 1} in input condition {'IL12': 0, 'IFNb': 0, 'IL18': 0, 'TCR': 1} is
0.7320523549275224
...
reduction of NoPA_predicted by control {'GATA3': 1} is
10.809676204819274
```
- The first line confirms the file address for the structural network model.
- The second line reaffirms the applied control.
- The third line confirms the FVS search method. If ```--find_minimum_FVSs True``` was used, it displays: this algorithm will find minimum FVSs using brute force search.
- The subsequent lines display 'reduction of NoPA_predicted' calculated under specific input conditions. Input nodes refer to nodes with no in-coming edges, and an input condition specifies each input node's Boolean value. In this example, there are four input nodes: 'IL12', 'IFNb', 'IL18', and 'TCR', creating a total of 16 possible input conditions.
- Finally, the sum of 'reduction of NoPA_predicted' across all input conditions provides the overall 'reduction of NoPA_predicted' value.
