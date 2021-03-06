# -*- coding: utf-8 -*-
"""Copy of RForest_Fastai_hyptune.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EXO52baZ0fo5FClOP8K4UNS9wz6fnrM9
"""

!pip install fastai==0.7.0

from fastai.imports import*
from fastai.structured import *
from pandas_summary import DataFrameSummary
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from IPython.display import display
from sklearn import metrics

# Load the Drive helper and mount
from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
df_raw = pd.read_csv("/content/PyDatadDrive/Train.csv")

df_raw.head().transpose()

def display_all(df):
    with pd.option_context("display.max_rows", 1000, "display.max_columns", 1000): 
        display(df)

display_all(df_raw.transpose())

df_raw.isnull().sum().sort_index().head()

df_raw.SalePrice = np.log(df_raw.SalePrice)

df_raw.dtypes

"""###  Data Preprocessing"""

add_datepart(df_raw, 'saledate')

df_raw.dtypes

"""- **The next step is to convert the categorical variables into numbers. We can use the train_cats function from fastai for this**"""

# %time train_cats(df_raw)

"""- **converting categorical to numeric columns**"""

# To change the order of the Order
df_raw.UsageBand.cat.set_categories(['High', 'Medium', 'Low'], ordered=True, inplace=True)

"""#### Missing Value Treatment"""

#  To look at the number of missing values in the dataset 
#  We use .isnull().sum() to get the total number of missing values. This is divided by the length of the dataset to determine the ratio of missing values.
# %time display_all(df_raw.isnull().sum().sort_index()/len(df_raw))

# We will save it in a feather format, as this let’s us access the data efficiently:
#to save
# os.makedirs('tmp', exist_ok=True)
# df_raw.to_feather('tmp/bulldozers-raw1')

#to read
import feather

df_raw = feather.read_dataframe('/content/PyDatadDrive/tmp/bulldozers-raw')

"""### impute the missing values and store the data as dependent and independent part
- using the fastai function ** proc_df **
"""

def split_vals(a,n):
   return a[:n].copy(), a[n:].copy()

df_trn, y_trn, nas = proc_df(df_raw, 'SalePrice', subset=30000)
X_train, X_valid = split_vals(df_trn, 20000)
y_train, y_valid = split_vals(y_trn, 20000)

X_train.shape, y_train.shape, X_valid.shape

"""### Building a single tree
- Random Forest is a group of trees which are called estimators. 
- The number of trees in a random forest model is defined by the parameter n_estimator.
- We will first look at a single tree (set n_estimator = 1) with a maximum depth of 3.
"""

m = RandomForestRegressor(n_estimators=1, max_depth=3, bootstrap=False, n_jobs=-1)
# %time m.fit(X_train, y_train)

def print_score(m):
    res = [rmse(m.predict(X_train), y_train),
           rmse(m.predict(X_valid), y_valid),
           m.score(X_train, y_train), m.score(X_valid, y_valid)]
    if hasattr(m, 'oob_score_'): res.append(m.oob_score_)
    print(res)

#define a function to check rmse value
def rmse(x,y): 
    return math.sqrt(((x-y)**2).mean())

print_score(m)

"""### ploting the tree"""

draw_tree(m.estimators_[0], df_trn, precision=3)

"""### Bagging
- In the bagging technique, we create multiple models, each giving predictions which are not correlated to the other.
- Then we average the predictions from these models. Random Forest is a bagging technique.

- If all the trees created are similar to each other and give similar predictions, then averaging these predictions will not improve the model performance. Instead, ** we can create multiple trees on a different subset of data, so that even if these trees overfit, they will do so on a different set of points**. These samples are taken with replacement.

- In * simple words* , ** we create multiple poor performing models and average them to create one good model**. The individual models must be as predictive as possible, but together should be uncorrelated. We will now increase the number of estimators in our random forest and see the results.
"""

m = RandomForestRegressor(n_jobs=-1) # If we do not give a value to the n_estimator parameter, it is taken as 10 by default.
# %time m.fit(X_train, y_train)
print_score(m)

# Further, np.stack will be used to concatenate the predictions one over the other.
preds = np.stack([t.predict(X_valid) for t in m.estimators_])

preds.shape

"""- o/p: This means we have 10 predictions for each row in the validation set.

Now for comparing our model’s results against the validation set, here is the row of predictions, the mean of the predictions and the actual value from validation set.
"""

preds[:,0], np.mean(preds[:,0]), y_valid[0]

plt.plot([metrics.r2_score(y_valid, np.mean(preds[:i+1], axis=0)) for i in range(10)]);

"""** The r^2 becomes better as the number of trees increases** . 
- You can experiment with the n_estimator value and see how the r^2 value changes with each iteration. 
- You’ll notice that after a certain number of trees, the r^2 value plateaus.
"""

m = RandomForestRegressor(n_estimators=20,n_jobs=-1) # If we do not give a value to the n_estimator parameter, it is taken as 10 by default.
# %time m.fit(X_train, y_train)
print_score(m)

# Further, np.stack will be used to concatenate the predictions one over the other.
preds = np.stack([t.predict(X_valid) for t in m.estimators_])

preds.shape

preds[:,0], np.mean(preds[:,0]), y_valid[0]

plt.plot([metrics.r2_score(y_valid, np.mean(preds[:i+1], axis=0)) for i in range(20)]);

"""### Out-of-Bag (OOB) Score
* Creating a separate validation set for a small dataset can potentially be a problem since it will result in an even smaller training set. In such cases, we can use the data points (or samples) which the tree was not trained on.

For this, ** we set the parameter oob_score =True.**
"""

m = RandomForestRegressor(n_estimators=40, n_jobs=-1, oob_score=True)
# %time m.fit(X_train, y_train)
print_score(m)

"""### Subsampling
* Earlier, we created a subset of 30,000 rows and the train set was randomly chosen from this subset. 
- As an alternative, we can create a different subset each time so that the model is trained on a larger part of the data.
- We use ** set_rf_samples **  to specify the sample size.
- ** reset_rf_samples()** # to reset back to normal
"""

set_rf_samples(20000)

m = RandomForestRegressor(n_estimators=40, n_jobs=-1, oob_score=True)
# %time m.fit(X_train, y_train)
print_score(m)

# reset back to normal and check the difference
reset_rf_samples()
m = RandomForestRegressor(n_estimators=40, n_jobs=-1, oob_score=True)
# %time m.fit(X_train, y_train)
print_score(m)

"""### Hyperparameters
  - ** Min sample leaf**:This can be treated as the *stopping criteria for the tree*. 
  - The ** tree stops growing (or splitting) when the number of samples in the leaf node is less than specified**.
"""

m = RandomForestRegressor(n_estimators=40, min_samples_leaf=3,n_jobs=-1, oob_score=True)
# %time m.fit(X_train, y_train)
print_score(m)

"""#### Max feature
- Another important parameter in random forest is ** max_features**. 
- We have discussed previously that the individual trees must be as uncorrelated as possible. 
- For the same,** random forest uses a subset of rows to train each tree. Additionally** , we can **also use a subset of columns (features) instead of using all the features**. 
- This is achieved by tweaking the **max_features parameter**.
"""

m = RandomForestRegressor(n_estimators=40, min_samples_leaf=3, max_features=0.5, n_jobs=-1, oob_score=True) 
# %time m.fit(X_train, y_train)
print_score(m)

# Further, np.stack will be used to concatenate the predictions one over the other.
preds = np.stack([t.predict(X_valid) for t in m.estimators_])

preds.shape

preds[:,0], np.mean(preds[:,0]), y_valid[0]

plt.plot([metrics.r2_score(y_valid, np.mean(preds[:i+1], axis=0)) for i in range(40)]);







