# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import math
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error

scaler = MinMaxScaler(feature_range=(0, 1))

def get_dataframe(data_path):
    return pd.read_csv(data_path)


def create_dataset(dataframe, lookback):
    dataX, dataY = [], []
    for i in range(len(dataframe) - lookback - 1):
        dataX.append(dataframe[i:(i+lookback), 0])
        dataY.append(dataframe[i+lookback, 0])
    return np.array(dataX), np.array(dataY)

def create_testset(dataframe, lookback):
    dataX = []
    for i in range(0, len(dataframe), lookback):
        dataX.append(dataframe[i:(i+lookback), 0])
    return np.array(dataX)


def normalize_data(dataset):
    dataset = dataset.values.reshape(-1, 1)
    dataset = scaler.fit_transform(dataset)
    return dataset

def create_lstm_model(trainX,trainY,look_back):
    model = Sequential()
    model.add(LSTM(16, input_shape=(1, look_back), activation='relu', return_sequences=True))
    model.add(LSTM(16, input_shape=(1, look_back), activation='relu'))
    model.add(Dense(1))
    model.compile(loss='mean_absolute_error', optimizer='adam')
    model.fit(trainX, trainY, epochs=150, batch_size=2, verbose=1)
    return model

def calcu_score(PredictY, groundtruth):
    weights = groundtruth[1]
    for i in range(len(weights)):
        if weights[i] == 0:
            weights[i] = 1
        else:
             weights[i] = 5
    score = sum(abs(PredictY-groundtruth[0])*weights)/sum(weights)
    print('Test Score: %f mae:',score)
    
def split_data(dataset):
    train_size = int(len(dataset) * 0.7)
    return dataset[0:train_size], dataset[train_size:len(dataset)]

#save the output
def write(y,store,dept,dates):
    f = open('result.csv','a')
    for i in range(len(y)):
        Id = str(store)+'_'+str(dept)+'_'+str(dates[i])
        sales = y[i]
        f.write('%s,%s\n'%(Id,sales))
    f.close()

if __name__ == '__main__':
    f = open('result.csv','w')
    f.write('Id,Weekly_Sales\n')
    lookback = 7
    trainframe = get_dataframe('train.csv')
    testframe = get_dataframe('test.csv')
    
    #get testdata
    for i in range(4,46):
        traindata = trainframe[trainframe.Store == i]
        testdata = testframe[testframe.Store == i]
        dept_train = list(set(traindata.Dept.values))
        dept_test = list(set(testdata.Dept.values))
        
        for dept in dept_test:
            if dept not in dept_train:
                tests = testdata[testdata.Dept == dept]
                dates = list(tests.Date)
                y=[0 for j in range(len(tests))]
                write(y,i,dept,dates)
                print(i,dept)
                continue  
            
            trains = traindata[traindata.Dept == dept]
            tests = testdata[testdata.Dept == dept]
            
            if(len(trains)<=20):
                print(len(trains))
                testY = []
                dates = list(tests.Date)
                for date in dates:
                    temp = date.split('-')
                    y,m,d = int(temp[0]),int(temp[1]),int(temp[2])
                    ymd = datetime.date(y,m,d)
                    week = datetime.timedelta(days=7)
                    last_year = str(ymd-52*week)
                    if last_year in trains.Date.tolist():
                        testY.append(trains.Weekly_Sales[trains.Date == last_year].values[0])
                    else:
                        testY.append(0)
                write(testY,i,dept,dates)
                continue
                
            train_sales = normalize_data(trains.Weekly_Sales)
            trainX,trainY = create_dataset(train_sales, lookback)
            trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
            
            testX = []
            for date in tests.Date:
                last_years = []
                temp = date.split('-')
                y,m,d = int(temp[0]),int(temp[1]),int(temp[2])
                ymd = datetime.date(y,m,d)
                week = datetime.timedelta(days=7)
                for k in range(lookback, 0, -1):
                    last_years.append(str(ymd-(k+52)*week))
                for last_year in last_years:
                    if last_year in trains.Date.tolist():
                        testX.append(trains.Weekly_Sales[trains.Date == last_year].values[0])
                    else:
                        testX.append(0)
#                testX.append(sales)
                        
            testX = {'sales':testX}
            testX = pd.DataFrame(testX)
            testX = normalize_data(testX)
            testX = create_testset(testX, lookback)
            testX = np.reshape(testX, (testX.shape[0],1,testX.shape[1]))
            model = create_lstm_model(trainX,trainY,lookback)
            testpredict = model.predict(testX)
            testpredict = scaler.inverse_transform(testpredict)
            dates = tests.Date.tolist()
            write(testpredict[:,0],i,dept,dates)
            print('Store:',i,'dept:',dept,'finished')
    
#    train, test = split_data(traintest)
#    
#    
#    train_sales = train.Weekly_Sales
#    train_sales = normalize_data(train_sales)
#    trainX,trainY = create_dataset(train_sales, lookback)
#    trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
#    model = create_lstm_model(trainX,trainY,lookback)
#    testY = []
#    groundtruth = [test.Weekly_Sales.values, test.IsHoliday.values.astype(int)]
#    for ind in test.index:
##        testX = []
##        testX.append(train.Weekly_Sales[ind-51-3:ind-51])
#        testX = train.Weekly_Sales[ind-51-1-143*2:ind-51-143*2]
##        testX = {'sales':testX}
##        testX = pd.DataFrame(testX)
#        testX = normalize_data(testX)
#        testX = np.transpose(testX)
#        testX = np.reshape(testX, (testX.shape[0],1,testX.shape[1]))
#        testpredict = model.predict(testX)
#        testpredict = scaler.inverse_transform(testpredict)
#        testY.append(testpredict[0][0])
#    calcu_score(np.array(testY),groundtruth)
#    
    
    