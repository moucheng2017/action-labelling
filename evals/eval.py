"""
demonstration-collection/experiments/eval/eval.py

This script is utilized to perform automatic evaluation of the generated SOPs
through comparison with the gold standard SOPs. Various evaluation metrics are
calculated and logged in a CSV file.
"""

import sys
import os
import concurrent.futures
import random
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import os
from tqdm import tqdm
from metrics import PairwiseComparison


def read_labels(folder_path):
    label_path = [f for f in os.listdir(folder_path) if f.endswith(".txt")][0]
    label_path = os.path.join(folder_path, label_path)
    try:
        labels = open(label_path, "r").read()
        # print(f"Read labels from {label_path}:")
        # print(labels)
        return labels
    except Exception as e:
        print(f"Error reading {label_path}: {e}")
        return None


# PREPROCESSING ===============================================================
def preprocess_sop(sop: str, data: dict) -> List[str]:
    """
    Given a SOP, this function preprocesses the SOP and returns a list of
    sentences.

    Args:
      sop (str): The SOP to be preprocessed

    Returns:
      List[str]: A list of sentences
    """
    # Split lines by newline character
    lines = sop.split("\n")

    # Remove empty lines
    lines = [line for line in lines if line.strip() != ""]

    # Cleanup the format, for each line, remove leading symbols until it starts with a number:
    lines = [line.lstrip(" -") for line in lines]
    lines = [line.lstrip(" *") for line in lines]
    lines = [line.lstrip(" .") for line in lines]
    lines = [line.lstrip(" ") for line in lines]

    # Remove lines that doesn't start with a number
    # lines = [line for line in lines if line.strip()[0].isdigit()]

    # assert if lins are empty
    assert len(lines) > 0, "SOP is empty"

    # If the line starts with * or -, remove it
    # lines = [line[1:] if line[0] in ["*", "-"] else line for line in lines]
    # lines = [line[1:] if line[0] in ["*", "-"] else line for line in lines]

    # Remove lines that doesn't start with a number
    # lines = [line for line in lines if line.strip()[0].isdigit()]

    # For each line, find the first instance of "." and keep everything after that
    # lines = [line[line.find(".") + 1 :] for line in lines]

    # # Remove any leading or trailing whitespace
    lines = [line.strip() for line in lines]

    # # Remove line if it is empty
    lines = [line for line in lines if len(line) > 0]

    # Print the preprocessed SOP
    # print("\n".join(lines))
    # print("\n\n\n")

    return lines


# LLM INFRA ===============================================================


def _check_sop(sop_dict) -> dict | None:
    try:
        pred_sop = preprocess_sop(sop_dict["pred_sop"], sop_dict)
        gold_sop = preprocess_sop(sop_dict["gold_sop"], sop_dict)
        return None
    except AssertionError:
        return sop_dict


def _evaluate_sops(sop_dict):
    """Helper function to evaluate a single pair of SOPs. Çalled in parallel in `evaluate_sops`."""

    # print(sop_dict["experiment_name"])
    # print(type(sop_dict["experiment_name"]))

    # Preprocess the SOPs
    pred_sop = preprocess_sop(sop_dict["pred_sop"], sop_dict)
    gold_sop = preprocess_sop(sop_dict["gold_sop"], sop_dict)

    # Create a cache_id for saving prompt eval results
    cache_id: str = (
        sop_dict["experiment_name"]
        + "_"
        + (
            sop_dict["demo_name"] + "_" + sop_dict["ablation"]
            if "demo_name" in sop_dict and "ablation" in sop_dict
            else random.randint(0, 1000000)
        )
    )
    del sop_dict["experiment_name"]

    # Create a PairwiseComparison
    pair_comp = PairwiseComparison(
        pred_sop=pred_sop, ref_sop=gold_sop, cache_id=cache_id
    )

    # Add metrics
    metrics: Dict[str, Any] = {
        "precision": pair_comp.precision(),
        "recall": pair_comp.recall(),
        "ordering": pair_comp.ordering(),
        "n_lines_pred_sop": len(pred_sop),
        "n_lines_gold_sop": len(gold_sop),
    }

    # Add all other key value pairs from the input dict
    metrics.update(sop_dict)

    return metrics


def evaluate_sops(
    list_of_sops: List[Dict[str, str]], experiment_name: str, n_threads: int = 10
) -> pd.DataFrame:
    """
    Given an input list of dictionaries containing generated SOPs and corresponding
    references, this function evaluates the generated SOPs and returns a list of
    dictionaries containing the evaluation metrics.

    Args:
      list_of_sops (List[Dict[str, str]]): A list of dictionaries containing
        generated SOPs and corresponding references.
        Each dictionary contains the following required items:
        - "pred_sop" (str): The generated SOP
        - "gold_sop" (str): The gold standard SOP
        And the following optional items:
        - "id" (str): The id for this unique demo pair

    Returns:
        pd.DataFrame: A pandas dataframe containing the columns:
        - "id" (str): The id for this unique demo pair
        - "precision" (float): The precision score
        - "recall" (float): The recall score
        - "ordering" (float): The ordering score
        - all other key value pairs from the input dict
    """
    # Iterate over each SOP dict
    results: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = [
            executor.submit(
                _evaluate_sops, sop_dict | {"experiment_name": experiment_name}
            )
            for idx, sop_dict in enumerate(list_of_sops)
        ]
        with tqdm(total=len(list_of_sops), desc="Evaluating SOPs") as pbar:
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                pbar.update(1)
    return pd.DataFrame(results)


def add_gold_sops(df_all_results: pd.DataFrame, path_to_demos_dir: str) -> pd.DataFrame:
    """Add Gold SOPs to the `df_all_results` dataframe.
    `path_to_demos_dir` is the path to the directory containing all the demos."""
    gold_sops: List[str] = []
    for idx, row in df_all_results.iterrows():
        # Collect the current demo name
        demo_name: str = row["demo_name"]

        # Ensure the folder exists
        if not os.path.exists(os.path.join(path_to_demos_dir, demo_name)):
            print(f"Error: `{demo_name}` does not exist")
            continue

        # Collect the contents of the folder
        folder_contents = os.listdir(os.path.join(path_to_demos_dir, demo_name))

        # Ensure exactly one file starts with "SOP"
        sop_files = [f for f in folder_contents if f.startswith("SOP")]
        if len(sop_files) != 1:
            print(f"Error: `{demo_name}` has {len(sop_files)} SOP files")
            continue

        # Create gold sop path file location
        gold_sop_file_path: str = os.path.join(
            path_to_demos_dir, demo_name, sop_files[0]
        )

        # Read in the contents of the gold SOP file as string
        with open(gold_sop_file_path, "r") as f:
            gold_sop: str = f.read().strip()

        # If first line doesn't start with a number, then remove b/c it's a title rather than a step
        if not gold_sop.split("\n")[0][0].isdigit():
            gold_sop = "\n".join(gold_sop.split("\n")[1:])

        # Save the gold SOP string to the df_all_results dataframe
        gold_sops.append(gold_sop)
    df_all_results["gold_sop"] = gold_sops
    return df_all_results


if __name__ == "__main__":
    # ==========================================================================================
    # Change here:
    # ==========================================================================================
    # set up openai api key in terminal:
    # export OPENAI_API_KEY="your-key"
    gt_folder = "/home/moucheng/projects/screen_action_labels/data/Wonderbread/gold_demos" # path too the ground truth folder
    task_name = "Wonderbread_gold_demos_507" # name of the task, used for saving the results
    predictions_folder = ["/home/moucheng/projects/screen_action_labels/results/1726068460/Wonderbread/gold_demos"] # list of paths to the predictions folder
    # ==========================================================================================
    # ==========================================================================================
    
    for prediction in predictions_folder:
        ablation = prediction.split("/")[-3]
        print('Starting evaluation of: ', ablation)
        # evaluate_predictions(prediction, gt_folder, task_name, ablation)

        # Get all videos from predictions folder
        all_videos = os.listdir(prediction)  
        all_videos.sort()

        # if test_no is not None:
        #     all_videos = all_videos[:test_no]
        
        # Create list to store collected SOP pairs
        sops = []

        # For each video in the predictions folder:
        for i, video in tqdm(enumerate(all_videos)):
            prediction_path = os.path.join(prediction, video, "label_prediction.txt")
            gt_path = os.path.join(gt_folder, video)
            gold_sop = read_labels(gt_path)
            
            # Load the prediction
            with open(prediction_path, "r") as f:
                pred_sop = f.read()
            
            # remove first line which is a title in both pred_sop and gold_sop
            gold_sop = "\n".join(gold_sop.split("\n")[1:])
            # pred_sop = "\n".join(pred_sop.split("\n")[1:])
            
            # Check if pred_sop is empty or gold_sop is empty:
            if pred_sop != "" and gold_sop != "":
                # Add an instance with rank_2 as the pred_sop and rank_1 as the gold_sop
                video = video.replace("@", "")
                video = video.replace(" ", "-") 
                sops.append(
                    {
                        "pred_sop": pred_sop,
                        "gold_sop": gold_sop,
                        "cache_id": task_name,
                        "demo_name": video,
                        "ablation": ablation
                    }
                )

        results = evaluate_sops(list_of_sops=sops, experiment_name=task_name)

        # save the results csv into the prediction_folder:
        save_folder = "/".join(prediction.split("/")[:-2])
        # make a subfolder called evals + timestamp:
        import time
        time = int(time.time())
        save_folder = os.path.join(save_folder, "evals" + str(time)) 
        os.makedirs(save_folder, exist_ok=True)
        # sort the results by demo_name:
        results = results.sort_values(by="demo_name")
        results.to_csv(os.path.join(save_folder, "results_evals_full.csv"), index=False)

        # from results only get columns: demo_name, ablation, precision, recall, ordering:
        results = results[["demo_name", "ablation", "precision", "recall", "ordering"]]
        # add a new row in the bottom by copying the last row:
        results.loc[len(results)] = results.iloc[-1]
        # change the "demo_name" of the last row to "average":
        results.loc[len(results)-1, "demo_name"] = "average"
        # for precision, recall, ordering, calculate the average and put in the last row:
        results.loc[len(results)-1, "precision"] = results["precision"].mean()
        results.loc[len(results)-1, "recall"] = results["recall"].mean()
        results.loc[len(results)-1, "ordering"] = results["ordering"].mean()
        results.to_csv(os.path.join(save_folder, "results_evals_simple.csv"), index=False)

        # print the results:
        print(results)

        print("Evaluation completed for: ", ablation)
        print("Results saved in: ", save_folder)
        print("=====================================================================")
  