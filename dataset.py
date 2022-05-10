import numpy as np
import pandas as pd
from constants import INTERESTED_BEATMAP_TYPE, PLAYER_DATA_COLS, ROUNDS
from copy import deepcopy as copy
from sklearn.pipeline import Pipeline


class Dataset():
    def __init__(self, csv_dir) -> None:
        self.read_csv(csv_dir)
    
    def read_csv(self, csv_dir):
        self.csv_dir = csv_dir
        self.data = pd.read_csv(csv_dir)
    
    @staticmethod
    def filter_out(a: list, b: list):
        return list(filter(lambda x: x not in b, a))
    
    @staticmethod
    def get_list_with_string(a: list, s: str):
        return list(filter(lambda x: s in x, a))


    def get_beatmap_columns(self, round=None, beatmap_type=None, numeric=False):
        columns = list(self.data.columns)
        def is_column(c):
            in_interested_type = False
            for t in INTERESTED_BEATMAP_TYPE:
                if t in c:
                    in_interested_type = not in_interested_type
                    break
            return (not round or c.split("_")[0] == round) and (not beatmap_type or (beatmap_type in c)) and (c not in self.get_unplayed_maps() + PLAYER_DATA_COLS) and in_interested_type
        
        
        columns = list(filter(is_column, columns))

        if not numeric:
            return PLAYER_DATA_COLS + columns
        return columns
    
    def __getitem__(self, *a):
        t = copy(self)
        t.data = t.data.__getitem__(*a)
        return t

    def get_unplayed_maps(self):
        unplayed_maps = []
        for column in self.data.columns:
            if column in PLAYER_DATA_COLS:
                continue
            if np.all(np.isnan(self.data[column].values)):
                unplayed_maps.append(column)
        return unplayed_maps
    
    def remove_unplayers(self):
        new_data = self.data.copy()
        for player in self.data['player_name']:
            player_data = self.data[self.data['player_name'] == player]
            if np.all(np.isnan(player_data[self.filter_out(player_data.columns, PLAYER_DATA_COLS)])):
                new_data = new_data[new_data['player_name'] != player]
        self.data = new_data
        
    def query(self, round=None, beatmap_type=None, numeric=False):
        a = self.get_beatmap_columns(round, beatmap_type, numeric)
        return self[a]
    
    def apply_outlier_model(self, round: str, beatmap_type: str, eda_model: Pipeline, outlier_model):
        dataset = self.query(round=round, beatmap_type=beatmap_type)
        dataset.remove_unplayers()
        players = dataset.data['player_name']
        dataset = dataset.query(numeric=True)
        pca_res = eda_model.fit_transform(dataset.data.values)
        outlier_res = outlier_model.fit_predict(pca_res)

        return players, pca_res, outlier_res