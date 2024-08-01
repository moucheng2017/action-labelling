## Introduction
This project focuses on improving the LMM's ability at low-level understanding of workflows. The key idea is to learn to ensemble the predictions of individually fine-tuned LMMs, of which is fine-tuned with different training samples. It is known that more training samples result in better fine-tuned model. However the context window length limits the number of the training samples. We expect that, ensembling the predictions is equivalent to ensembling the training samples in order to breakthrough the context window length limit.  

## Methods
The current pipeline only has the in-context learning part. The LMM observes a few training examples as prompts first. Then the LMM got asked to predict for new cases. See the below sections of prompts for more details.

## Install the libraries
Given that you have installed python==3.11.2. If you don't have virtual environment, then install it via following lines. Specifiy your own "your_project_directory".
```bash
pip install virtualenv
cd your_project_directory
virtualenv venv
virtualenv -p python venv
python -m venv venv
```
If you already have virtual environment, install the libraries via the following lines. You can change "myenv" to your own choice. You are welcome to use conda but conda might take more spaces.
```bash
virtualenv -p python myenv
python -m venv venv
```

## Data
We are currently using a toy dataset of screenshots of user actions on Notepad application. Download the dataset from beneath google drive link:
https://drive.google.com/drive/folders/1TSO4qZZniJVwQDs99udxMd_G9nNJii9p?usp=drive_link

The above dataset is structured as:
```
data_directory/
│
├── training/
│ ├── video1/
│ │ ├── screenshots/
│ │ │ │ ├── image1.png
│ │ │ │ ├── image2.png
│ │ │ │ ├── image3.png
│ │ ├── label.txt
│ ├── video2/
│ ├── video3/
...
├── testing/
│ ├── video1/
│ │ ├── screenshots/
│ │ │ │ ├── image1.png
│ │ │ │ ├── image2.png
│ │ │ │ ├── image3.png
│ ├── video2/
│ ├── video3/
...
```

The dataloader reads a txt file for videos so that we can arbitrary data splits without saving the data for each split.

## How to start with this git repo:
Please have a closer look at the default config file in "configs/example.yml". To run the current pipeline, you can run the main function via:
```bash
cd your_own_working_directory_of_this_repository
python main.py --config configs/example.yml
```
Modify the config file to your own specifications. The used config files will always be saved in the result folder so you can always reproduce your results. It is suggested to create new config files for new experiments. Feel free to experiment any cool prompts you want!

## How to start new tasks within this repo:
1. Go to "Issues" on the github repo: https://github.com/mcx-agile-loop/action-labelling/issues
2. Create a new issue with whatever your new task is
3. Create a new branch from the new issue
4. Work on your own branch

Always make sure your are using the latest git repo by "git fetch" and always work on your own local branch.

<!-- ## The current prompts for training:
```
You are a labelling assistant to label the user interactions with the screen for every screenshot in the chronological screenshots. Each screenshot is a state of the screen at a certain time. The label for each state should only describe the user's last actions which changed the last state of the screen to the current state of the screen. 
Each screenshot should have one label. In each label, describe: the user action just happened, the screen display change, and the current screen display.
Do not skip any intermediate actions.
Be specific, precise and accurate.

The following is {number_frames} chronological screenshots and their labels:
{image0.png}
{image1.pmng}
...
{image24.pnt}

The following is the labels for the above sequence of screenshots:
label0
label1
...
label24

``` -->

<!-- ## The current prompts for testing:
```
The following is {number_frames} chronological screenshots:
{image0.png}
{image1.pmng}
...
{image10.pnt}

Please provide the labels for each state in the above screenshots by fulfilling the beneath template:
---START FORMAT TEMPLATE---
State0:
State1:
...
State10:
---END FORMAT TEMPLATE---
Do not deviate from the above format.
``` -->

## The current prompts for self-reflection:
```
The initial prediction is:
{initial_prediction}
Please review the screenshots and their prediction. Provide an improved version of the prediction if necessary.
```

## Evaluation
In the subfolder called evals, change the parameters in the evals.py first. Set up the api key then run the eval.py.
```
export OPEN_API_KEY="some-some-key"
python evals/eval.py
```

## Contacts
Contact Moucheng Xu for any questions: xumoucheng28@gmail.com