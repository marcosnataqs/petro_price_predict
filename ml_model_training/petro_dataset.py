import os
import pandas as pd
import numpy as np
import torch

from joblib import dump
from torch.utils.data import Dataset
from sklearn.preprocessing import MinMaxScaler


class PetroDataset(Dataset):
    """
    The PetroDataset class requires you to make the train test split outside first without any prior treatment.
    After that the class will take care of everything else interactivelly as long as you pass the correct parameters in the constructor
    """

    def __init__(self, data: pd.DataFrame, pipeline_params: dict) -> None:
        """
        This initialize the Dataset class, important to notice that num_features param must NOT consider the index.
        """
        self.pipeline_params = pipeline_params
        self.data = data
        self.num_features = self.pipeline_params["num_features"]
        self.transform_data_pipeline()

    def transform_data_pipeline(self) -> None:
        """
        This is a custom method where will be implemented data transformations,
        the idea is to simply pass the crude data to the class and PetroDataset will take care od the test.
        """
        # self.add_lags()
        self.split_data()
        self.scale_data()
        self.reshape_data()

    # def add_lags(self) -> None:
    #     """
    #     This method will use the pipeline parameters to generate the lags for the columns I chose.
    #     This means that I can interate each every column I want and set a number or lags that I may use in my model later.
    #     """
    #     for column in self.pipeline_params["columns"]:
    #         for i in range(1, self.pipeline_params["num_lags"] + 1):
    #             self.data[f"{column}_(t-{i})"] = self.data[column].shift(i)
    #         self.num_features += self.pipeline_params["num_lags"]
    #     self.data.dropna(inplace=True)
    #     # self.data.drop(columns=['adj_pbr','brent','wti','production','usd'])
    #     # self.num_features -= 4

    def split_data(self) -> None:
        self.input_data = self.data.drop(columns='pbr', axis=1)
        #flip dataframe
        self.input_data = self.input_data.iloc[:, ::-1]
        self.output_data = self.data['pbr']
    
    def scale_data(self) -> None:
        """
        This method is used to scale my train data in the pipeline,
        it also saves my scaler as a joblib/pickle so it can be used later.
        """
        input_scaler_filename = os.path.join("ml_model_training", "input_scaler_petro.joblib")
        output_scaler_filename = os.path.join("ml_model_training", "output_scaler_petro.joblib")
        
        input_scaler = MinMaxScaler(feature_range=(-1, 1))
        output_scaler = MinMaxScaler(feature_range=(-1, 1))

        self.input_data = input_scaler.fit_transform(self.input_data)
        self.output_data = output_scaler.fit_transform(self.output_data.values.reshape(-1,1))

        # self.data_scaled = scaler.fit_transform(self.data)
        dump(input_scaler, input_scaler_filename)
        dump(output_scaler, output_scaler_filename)

    def reshape_data(self) -> None:
        """
        Ths method will reshape my data spliting the target from the data.
        It also adjusts the dimensions of the numpy array so it matches the required dimensions for LSTM
        """
        #X = np.flip(self.input_data, axis=1)
        X = self.input_data
        y = self.output_data
        self.X = X.reshape((-1, (self.num_features), 1))
        self.y = y.reshape((-1, 1))
        print(self.X.shape, self.y.shape)
        print(type(self.X), type(self.y))

    def __len__(self) -> int:
        """
        Standard method from Dataset which is responsible for returning the len of my Dataset
        """
        return len(self.data)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Standard method from Dataset, where I am first retrieving my data as per index.
        After that I am transforming it into a Tensor so it can be consumed in LSTM
        """
        X = self.X[idx]
        y = self.y[idx]
        ## convert to tensor
        X = torch.from_numpy(X.astype(np.float32))
        y = torch.from_numpy(y.astype(np.float32))
        return X, y


if __name__ == "__main__":
    from data_engineering.data_utils import add_lags
    data = pd.read_csv(
        os.path.join("ml_model_training", "petro_2.csv"), index_col=0, parse_dates=True
    ).sort_index()
    data = add_lags(data, 7, columns=['pbr'])
    params = {"num_features": 7}
    petrodata = PetroDataset(data, pipeline_params=params)
    data, target = petrodata[1]
    print(data, target)
