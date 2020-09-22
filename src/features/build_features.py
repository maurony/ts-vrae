# general
import sys
import os
import shutil
import glob
from pathlib import Path
from tqdm import tqdm
import json

# logging
import logging.config
import logging

# data structures
import numpy as np
import torch
import pandas as pd
import pyarrow.parquet as pq

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)


def process_resmed_train(
    user_data_path: str = "data/external/user_classification",
    data_path: str = "data/raw/resmed",
    output_path: str = "data/processed/resmed",
    seq_len: int = 750
) -> torch.Tensor:
    """generate training data using user classification config

    Args:
        user_data_path (str, optional): Path to user classification data. Defaults to "data/external/user_classification".
        data_path (str, optional): Path to data. Defaults to "data/raw/resmed".
        output_path (str, optional): Path for training set. Defaults to "data/processed/resmed".
        seq_len (int, optional): Sequence length for algorithm. Defaults to 750.

    Returns:
        [torch.Tensor]: Tensor in shape ()
    """

    # get configs
    configs = [p for p in Path(user_data_path).iterdir()]

    # make sure ouput path exists and is empty
    output_path = Path(output_path)

    # remove directories if they exist
    if output_path.exists():
        shutil.rmtree(output_path)

    output_path.mkdir(parents=True, exist_ok=True)

    # process data
    tensor_list = []

    with tqdm(total=len(configs), bar_format="{desc:<5.5}{percentage:3.0f}%|{bar:100}{r_bar}", ascii=True) as pbar:
        for config in configs:

            # read configuration file
            with open(config, "r") as f:
                config = json.load(f)

            pbar.set_postfix(file=str(os.path.basename(config["data_file"])))

            # create parquet table
            df = pq.read_table(
                os.path.join(data_path, os.path.basename(config["data_file"]))
            ).to_pandas()

            # get normal range from config
            if config["range"]["from"] is not None and config["range"]["to"] is not None:
                start_range = float(config["range"]["from"] * 60)
                end_range = float(config["range"]["to"] * 60)

                # filter data frame
                df = df[(df.time_offset >= start_range)
                        & (df.time_offset <= end_range)]

                # get tensor
                train_tensor = torch.Tensor(df.iloc[:, :3].values)
                # dims
                dims = train_tensor.shape
                # n sequences
                n_seq = dims[0] // seq_len
                # crop train tensor to match
                train_tensor = train_tensor[:(n_seq * seq_len), :]
                # reshape tensor
                train_tensor = train_tensor.view(n_seq, seq_len, dims[1])

                tensor_list.append(train_tensor)

            pbar.update(1)

    torch.save(torch.cat(tensor_list), os.path.join(output_path, "train.pt"))


def to_categorical(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Convert column to categorical

    Args:
        df (pd.DataFrame): input data frame
        col (str): column to be transformed

    Returns:
        pd.DataFrame: output data frame
    """
    # just do ignore warning...
    if df[col].dtype.name != 'category':
        df.loc[:, col] = df[col].astype('category')
    df.loc[:, col] = df[col].cat.codes.astype("int16")
    df.loc[:, col] -= df[col].min()
    return df
