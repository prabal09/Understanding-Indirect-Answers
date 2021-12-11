# -*- coding: utf-8 -*-
"""YN-QARelaxed.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QoPfUJ05T9Dcedni-f8xwCu37OhDYw-m

# Sentiment Analysis with Deep Learning using BERT

### Prerequisites

- Intermediate-level knowledge of Python 3 (NumPy and Pandas preferably, but not required)
- Exposure to PyTorch usage
- Basic understanding of Deep Learning and Language Models (BERT specifically)

### Project Outline

**Task 1**: Introduction (this section)

**Task 2**: Exploratory Data Analysis and Preprocessing

**Task 3**: Training/Validation Split

**Task 4**: Loading Tokenizer and Encoding our Data

**Task 5**: Setting up BERT Pretrained Model

**Task 6**: Creating Data Loaders

**Task 7**: Setting Up Optimizer and Scheduler

**Task 8**: Defining our Performance Metrics

**Task 9**: Creating our Training Loop

## Introduction

### What is BERT

BERT is a large-scale transformer-based Language Model that can be finetuned for a variety of tasks.

For more information, the original paper can be found [here](https://arxiv.org/abs/1810.04805). 

[HuggingFace documentation](https://huggingface.co/transformers/model_doc/bert.html)

[Bert documentation](https://characters.fandom.com/wiki/Bert_(Sesame_Street) ;)

<img src="Images/BERT_diagrams.pdf" width="1000">

## Exploratory Data Analysis and Preprocessing

We will use the SMILE Twitter dataset.

_Wang, Bo; Tsakalidis, Adam; Liakata, Maria; Zubiaga, Arkaitz; Procter, Rob; Jensen, Eric (2016): SMILE Twitter Emotion dataset. figshare. Dataset. https://doi.org/10.6084/m9.figshare.3187909.v2_
"""

import torch
import pandas as pd
from tqdm.notebook import tqdm
import csv
import numpy as np

# df = pd.read_csv('circa-data.tsv')
df = pd.read_csv('circa-data.tsv', delimiter="\t", encoding='utf-8',quoting=csv.QUOTE_NONE,usecols=['context','questionX','answerY','goldstandard1','goldstandard2'])
# df.set_index('id', inplace=True)

df.dropna(subset=["goldstandard2"], inplace=True)

df = df[df.goldstandard2 != 'Other']
print(len(df))

df.sample(5)

df.goldstandard2.value_counts()

import matplotlib.pyplot as plt
from matplotlib import cm

colors = cm.jet(np.linspace(0,1,5))
df.goldstandard2.value_counts().sort_values().plot(kind = 'barh',grid = True, legend = True,color=colors)

colors = cm.jet(np.linspace(0,1,10))
df.context.value_counts().sort_values().plot(kind = 'barh',grid = True,color=colors)

possible_labels = df.goldstandard2.unique()

possible_labels

label_dict = {}
for index, possible_label in enumerate(possible_labels):
    label_dict[possible_label] = index

label_dict

df['goldstandard2'] = df.goldstandard2.replace(label_dict)

df.head()

"""## Training/Validation Split"""

from sklearn.model_selection import train_test_split

X_train, X_val_test, y_train, y_val_test = train_test_split(df.index.values, 
                                                  df.goldstandard2.values, 
                                                  test_size=0.6, 
                                                  random_state=17, 
                                                  stratify=df.goldstandard2.values)
X_test, X_val, y_test, y_val = train_test_split(df.loc[X_val_test].index.values, 
                                                  df.loc[X_val_test].goldstandard2.values, 
                                                  test_size=0.5, 
                                                  random_state=17, 
                                                  stratify=df.loc[X_val_test].goldstandard2.values)

df['data_type'] = ['not_set']*df.shape[0]

df.loc[X_train, 'data_type'] = 'train'
df.loc[X_val, 'data_type'] = 'val'
df.loc[X_test,'data_type'] = 'test'

df.sample(5)

ans = df.groupby(['context']).count()

"""## Loading Tokenizer and Encoding our Data"""

!pip install transformers

from transformers import BertTokenizer
from torch.utils.data import TensorDataset

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', 
                                          do_lower_case=True)

encoded_data_train = tokenizer.batch_encode_plus(
    df[df.data_type=='train'].questionX.values  + '[SEP]' + df[df.data_type=='train'].answerY.values, 
    add_special_tokens=True, 
    return_attention_mask=True, 
    pad_to_max_length=True, 
    max_length=25, 
    return_tensors='pt'
)

encoded_data_val = tokenizer.batch_encode_plus(
    df[df.data_type=='val'].questionX.values  + '[SEP]' + df[df.data_type=='val'].answerY.values, 
    add_special_tokens=True, 
    return_attention_mask=True, 
    pad_to_max_length=True, 
    max_length=25, 
    return_tensors='pt'
)

encoded_data_test = tokenizer.batch_encode_plus(
    df[df.data_type=='test'].questionX.values  + '[SEP]' + df[df.data_type=='test'].answerY.values, 
    add_special_tokens=True, 
    return_attention_mask=True, 
    pad_to_max_length=True, 
    max_length=25, 
    return_tensors='pt'
)

input_ids_train = encoded_data_train['input_ids']
attention_masks_train = encoded_data_train['attention_mask']
labels_train = torch.tensor(df[df.data_type=='train'].goldstandard2.values)

input_ids_val = encoded_data_val['input_ids']
attention_masks_val = encoded_data_val['attention_mask']
labels_val = torch.tensor(df[df.data_type=='val'].goldstandard2.values)

input_ids_test = encoded_data_test['input_ids']
attention_masks_test = encoded_data_test['attention_mask']
labels_test = torch.tensor(df[df.data_type=='test'].goldstandard2.values)

# df[df.data_type=='train'].questionX.values  + '[SEP]' + df[df.data_type=='train'].answerY.values

dataset_train = TensorDataset(input_ids_train, attention_masks_train, labels_train)
dataset_val = TensorDataset(input_ids_val, attention_masks_val, labels_val)
dataset_test = TensorDataset(input_ids_test, attention_masks_test, labels_test)

len(dataset_train)

len(dataset_val)

len(dataset_test)

"""## Setting up BERT Pretrained Model"""

from transformers import BertForSequenceClassification

import torch.nn as nn

model = BertForSequenceClassification.from_pretrained("bert-base-uncased",
                                                      num_labels=len(label_dict),
                                                      output_attentions=False,
                                                      output_hidden_states=False)
#"ishan/bert-base-uncased-mnli"

model = BertForSequenceClassification.from_pretrained("ishan/bert-base-uncased-mnli",
                                                      num_labels=3,
                                                      output_attentions=False,
                                                      output_hidden_states=False)

model.classifier = nn.Linear(in_features=768, out_features=5, bias=True)
model.num_labels = 5

model

"""## Creating Data Loaders"""

from torch.utils.data import DataLoader, RandomSampler, SequentialSampler

batch_size = 32

dataloader_train = DataLoader(dataset_train, 
                              sampler=RandomSampler(dataset_train), 
                              batch_size=batch_size)

dataloader_validation = DataLoader(dataset_val, 
                                   sampler=SequentialSampler(dataset_val), 
                                   batch_size=batch_size)

dataloader_test = DataLoader(dataset_test, 
                                   sampler=SequentialSampler(dataset_test), 
                                   batch_size=batch_size)

"""## Setting Up Optimiser and Scheduler"""

from transformers import AdamW, get_linear_schedule_with_warmup

optimizer = AdamW(model.parameters(),
                  lr=3e-5, 
                  eps=1e-8)

epochs = 3

scheduler = get_linear_schedule_with_warmup(optimizer, 
                                            num_warmup_steps=0,
                                            num_training_steps=len(dataloader_train)*epochs)

"""## Defining our Performance Metrics

Accuracy metric approach originally used in accuracy function in [this tutorial](https://mccormickml.com/2019/07/22/BERT-fine-tuning/#41-bertforsequenceclassification).
"""

import numpy as np

from sklearn.metrics import f1_score

def f1_score_func(preds, labels):
    preds_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return f1_score(labels_flat, preds_flat, average='weighted')

def accuracy_per_class(preds, labels):
    label_dict_inverse = {v: k for k, v in label_dict.items()}
    
    preds_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    total_correct = 0;total_samples = 0
    for label in np.unique(labels_flat):
        y_preds = preds_flat[labels_flat==label]
        y_true = labels_flat[labels_flat==label]
        print(f'Class: {label_dict_inverse[label]}')
        print(f'Accuracy: {len(y_preds[y_preds==label])}/{len(y_true)}')
        print('Correct Predictions ', str(label) , len(y_preds[y_preds==label])/len(y_true))
        total_correct += len(y_preds[y_preds==label])
        total_samples += len(y_true)
    print('Total Correct Predictions ',total_correct/total_samples)

"""## Creating our Training Loop

Approach adapted from an older version of HuggingFace's `run_glue.py` script. Accessible [here](https://github.com/huggingface/transformers/blob/5bfcd0485ece086ebcbed2d008813037968a9e58/examples/run_glue.py#L128).
"""

import random

seed_val = 17
random.seed(seed_val)
np.random.seed(seed_val)
torch.manual_seed(seed_val)
torch.cuda.manual_seed_all(seed_val)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

print(device)

def evaluate(dataloader_val):

    model.eval()
    
    loss_val_total = 0
    predictions, true_vals = [], []
    
    for batch in dataloader_val:
        
        batch = tuple(b.to(device) for b in batch)
        
        inputs = {'input_ids':      batch[0],
                  'attention_mask': batch[1],
                  'labels':         batch[2],
                 }

        with torch.no_grad():        
            outputs = model(**inputs)
            
        loss = outputs[0]
        logits = outputs[1]
        loss_val_total += loss.item()

        logits = logits.detach().cpu().numpy()
        label_ids = inputs['labels'].cpu().numpy()
        predictions.append(logits)
        true_vals.append(label_ids)
    
    loss_val_avg = loss_val_total/len(dataloader_val) 
    
    predictions = np.concatenate(predictions, axis=0)
    true_vals = np.concatenate(true_vals, axis=0)
            
    return loss_val_avg, predictions, true_vals

for epoch in tqdm(range(1, epochs+1)):
    
    model.train()
    
    loss_train_total = 0

    progress_bar = tqdm(dataloader_train, desc='Epoch {:1d}'.format(epoch), leave=False, disable=False)
    for batch in progress_bar:

        model.zero_grad()
        
        batch = tuple(b.to(device) for b in batch)
        
        inputs = {'input_ids':      batch[0],
                  'attention_mask': batch[1],
                  'labels':         batch[2],
                 }       

        outputs = model(**inputs)
        
        loss = outputs[0]
        loss_train_total += loss.item()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()
        scheduler.step()
        
        progress_bar.set_postfix({'training_loss': '{:.3f}'.format(loss.item()/len(batch))})
         
        
    torch.save(model.state_dict(), f'finetuned_BERT_epoch_{epoch}.model')
        
    tqdm.write(f'\nEpoch {epoch}')
    
    loss_train_avg = loss_train_total/len(dataloader_train)            
    tqdm.write(f'Training loss: {loss_train_avg}')
    
    val_loss, predictions, true_vals = evaluate(dataloader_validation)
    val_f1 = f1_score_func(predictions, true_vals)
    tqdm.write(f'Validation loss: {val_loss}')
    tqdm.write(f'F1 Score (Weighted): {val_f1}')

_, predictions, true_vals = evaluate(dataloader_validation)

accuracy_per_class(predictions, true_vals)

from sklearn.metrics import classification_report

preds = np.argmax(predictions, axis=1).flatten()
target_names = ['Yes','No','In the middle, neither yes nor no','Yes, subject to some conditions']
print(classification_report(true_vals,preds,target_names=target_names,digits=3))

_, predictions, true_vals = evaluate(dataloader_test)

accuracy_per_class(predictions, true_vals)

preds = np.argmax(predictions, axis=1).flatten()
target_names = ['Yes','No','In the middle, neither yes nor no','Yes, subject to some conditions']
print(classification_report(true_vals,preds,target_names=target_names,digits=3))



#------load saved model then run--------

model = BertForSequenceClassification.from_pretrained("bert-base-uncased",
                                                      num_labels=len(label_dict),
                                                      output_attentions=False,
                                                      output_hidden_states=False)

model.to(device)

model.load_state_dict(torch.load('Models/<<INSERT MODEL NAME HERE>>.model', map_location=torch.device('cpu')))

_, predictions, true_vals = evaluate(dataloader_validation)

accuracy_per_class(predictions, true_vals)

preds = np.argmax(predictions, axis=1).flatten()
target_names = ['Yes','No','Yes, subject to some conditions','In the middle, neither yes nor no','Other']
print(classification_report(true_vals,preds,target_names=target_names))