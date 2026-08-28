import os

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class Ensemble_data:
    def __init__(self, address_save_folder=".\\ensemble_of_all_possible_nc_logics"):
        self.address_save_folder = address_save_folder
        self.logiccomb_results_map = {}

        self.index_logic_combination = None
        self.index_NoPA = None
        self.index_NoA = None
        self.index_att_land = None

        self._read_NoPA_from_save_folder()

        self.perturbation_NoPA_avg_map = {}

    def _read_NoPA_from_save_folder(self):
        file_names = os.listdir(self.address_save_folder)
        for file_name in file_names:
            if file_name == "model_regulators_order_information.txt":
                continue
            self._read_NoPA_of_one_perturbation(file_name)
    
    def _read_NoPA_of_one_perturbation(self, file_name):
        """read NoPA of one perturbation from the file_name.
        return a dataframe with columns of 'logics' and 'NoPA'"""
        address_file = os.path.join(self.address_save_folder, file_name)
        with open(address_file, 'r') as f:
            line_perturbation = f.readline()
            perturbation  = eval(line_perturbation.split('\t')[1])
            line_node_order = f.readline()    
            node_order  = eval(line_node_order.split('\t')[1])
            f.readline() # NoPA distribution for specific perturbation
            f.readline() # NoA distribution for specific perturbation

            column_line = f.readline().strip()
            if self.index_logic_combination is None:
                self._analyze_colums_line(column_line)            
            
            for line in f:
                self._analyze_result_line_and_put_to_result_obj(perturbation, line)

    def _analyze_colums_line(self, column_line):
        columns = column_line.split('\t')
        self.index_logic_combination = columns.index("logic_combination")
        self.index_NoPA = columns.index("NoPA")
        self.index_NoA = columns.index("NoA")
        self.index_att_land = columns.index("attractor_landscape")

    def _analyze_result_line_and_put_to_result_obj(self, perturbation_dict, result_line):
        line_splited = result_line.strip().split('\t')
        logic_comb = eval(line_splited[self.index_logic_combination])
        NoPA = int(line_splited[self.index_NoPA])
        NoA = int(line_splited[self.index_NoA])
        att_land = eval(line_splited[self.index_att_land])

        result_obj = self._get_Result_obj_for_logic_comb(logic_comb)
        data_dict = {"NoPA":NoPA, "NoA":NoA, "attractor_landscape":att_land}

        result_obj.put_dict_data(perturbation_dict, data_dict)

    def _get_Result_obj_for_logic_comb(self, logic_comb):
        if logic_comb in self.logiccomb_results_map:
            return self.logiccomb_results_map[logic_comb]
        else:
            result_obj = Result_for_logic_comb(logic_comb)
            self.logiccomb_results_map[logic_comb] = result_obj
            return result_obj

    def _calculate_NoPA_avg(self):
        perturbation_NoPA_sum_map = {}
        for result_logic_comb_obj in self.logiccomb_results_map.values():
            for perturbation_tuple, data_dict in result_logic_comb_obj.perturbation_result_map.items():
                NoPA = data_dict["NoPA"]
                perturbation_NoPA_sum_map[perturbation_tuple] = perturbation_NoPA_sum_map.get(perturbation_tuple, 0) + NoPA
        
        for perturbation_tuple, NoPA_sum in perturbation_NoPA_sum_map.items():
            NoPA_avg = NoPA_sum / len(self.logiccomb_results_map)
            self.perturbation_NoPA_avg_map[perturbation_tuple] = NoPA_avg
    
    def get_NoPA_avg_reduction(self):
        self._calculate_NoPA_avg()
        nominal = ()
        perturbation_NoPA_avg_reduction_map = {}
        for perturbation_tuple, NoPA_avg in self.perturbation_NoPA_avg_map.items():
            if perturbation_tuple == nominal:
                continue
            NoPA_avg_reduction = self.perturbation_NoPA_avg_map[nominal] - NoPA_avg
            perturbation_NoPA_avg_reduction_map[perturbation_tuple] = NoPA_avg_reduction

        return perturbation_NoPA_avg_reduction_map
    
    def get_true_NoPA_reduction_of_model(self, logic_comb):
        result_obj = self.logiccomb_results_map[logic_comb]
        nominal = ()
        perturbation_true_NoPA_reduction_map = {}
        for perturbation_tuple, data_dict in result_obj.perturbation_result_map.items():
            if perturbation_tuple == nominal:
                continue
            NoPA_reduction = result_obj.perturbation_result_map[nominal]["NoPA"] - data_dict["NoPA"]
            perturbation_true_NoPA_reduction_map[perturbation_tuple] = NoPA_reduction

        return perturbation_true_NoPA_reduction_map
    
    def draw_true_ava_NoPA_scatter_plot(self, logic_comb):
        perturbation_NoPA_avg_reduction_map = self.get_NoPA_avg_reduction()
        perturbation_true_NoPA_reduction_map = self.get_true_NoPA_reduction_of_model(logic_comb)

        perturbations = list(perturbation_NoPA_avg_reduction_map.keys())
        true_NoPA_reductions = [perturbation_true_NoPA_reduction_map[p] for p in perturbations]
        average_NoPA_reductions = [perturbation_NoPA_avg_reduction_map[p] for p in perturbations]

        df_NoPAs = pd.DataFrame({"control":perturbations, "true":true_NoPA_reductions, "average":average_NoPA_reductions})
        sns.lmplot(x="average",y="true", data=df_NoPAs, scatter_kws={"alpha":0.3})
        plt.ylabel("True NoPA reduction")
        plt.xlabel("Average NoPA reduction")

        for i, perturbation in enumerate(df_NoPAs["control"]):
            x_coor = df_NoPAs.loc[i, "average"]
            y_coor = df_NoPAs.loc[i, "true"]
            dot_name = str(perturbation)
            # print(x_coor, y_coor, dot_name)
            plt.text(x_coor, y_coor, dot_name, fontsize=8)
        
    

class Result_for_logic_comb:
    def __init__(self, logic_comb):
        self.logic_comb = logic_comb
        self.perturbation_result_map = {}
    
    def _convert_perturbation_dict_to_tuple(self, perturbation_dict):
        """convert perturbation dict to tuple form.
        perturbation_dict is a dictionary of node_name:perturbation_value"""
        perturbation_tuple = tuple(sorted(perturbation_dict.items()))
        return perturbation_tuple
    
    def _convert_perturbation_tuple_to_dict(self, perturbation_tuple):
        """convert perturbation tuple to dict form.
        perturbation_tuple is a tuple of (node_name, perturbation_value)"""
        perturbation_dict = dict(perturbation_tuple)
        return perturbation_dict
    
    def put_dict_data(self, perturbation_dict, data_dict):
        perturbation_tuple = self._convert_perturbation_dict_to_tuple(perturbation_dict)
        self.perturbation_result_map[perturbation_tuple] = data_dict