# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 11:30:41 2022

@author: bmaur
"""

from pywebio import *
from pywebio.output import *
from pywebio.input import *
from pywebio.pin import *
from cutecharts.charts import Bar
from cutecharts.faker import Faker
import pandas as pd
from pywebio import start_server
import numpy as np
import csv
import pandas as pd
def create_general_dict_from_csv():
    names = ['Origine ', 'CCN_USNEF', 'Transport_2019', 'Logistique_2019', 'Total_2019', 'Transport_2020', 'Logistique_2020', 'Total_2020', 'Cotis_2021', 'Normalement', 'Comments']
    dict_general = {}
    with open('C:\MISSION_EJE\donnes_remastered.csv') as csvfile:
        reader = csv.reader(csvfile, delimiter = ';')
        first_try = True
        for row in reader:
            if first_try:
                first_try = False
                continue
            dict_tampon = {}
            for i,elem in enumerate(row):
                if i == 0:
                    name = elem
                    continue
                try:
                    value = float(elem)
                except ValueError:
                    value = elem
                if elem == '':
                    value = 0
                if elem == 'OUI':
                    value = 1
                dict_tampon[names[i-1]] = value
            if dict_tampon['Transport_2019']>0 or dict_tampon['Logistique_2019']>0 or dict_tampon['Logistique_2020']>0 or dict_tampon['Transport_2020']>0:
                if name != 'STEF':
                    dict_general[name] = dict_tampon
    return dict_general

def clean_pandas():
    dict_for_pd = create_general_dict_from_csv()
    cotisations = pd.DataFrame.from_dict(dict_for_pd, orient='index')
    cotisations = cotisations.loc[:,['Transport_2019', 'Transport_2020', 'Logistique_2019', 'Logistique_2020', 'Cotis_2021', 'CCN_USNEF']]
    cotisations.Cotis_2021 = cotisations.Cotis_2021.astype(float)
    transport = []
    logistique = []
    for i in range(len(cotisations)):
        if pd.isna(cotisations['Transport_2019'][i]):
            transport.append(cotisations['Transport_2020'][i])
        else:
            transport.append(max(cotisations['Transport_2020'][i],cotisations['Transport_2019'][i]))
        if pd.isna(cotisations['Logistique_2019'][i]):
            logistique.append(cotisations['Logistique_2020'][i])
        else:
            logistique.append(max(cotisations['Logistique_2020'][i],cotisations['Logistique_2019'][i]))
    cotisations['Transport'] = transport
    cotisations['Logistique'] = logistique
    cotisations.to_csv('test_end_vrai.csv', sep = ';')
    return cotisations

def calc_transport(x):
    return 200+ 110*np.minimum(x,20) + 55*np.maximum(0,np.minimum(x-20,20)) + 45*np.maximum(0,x-40)

def calc_logistique(y):
    return 300*y*(1000/999)
    #return 500*y**(90/100)

def calc_new_cotis(x,y,z):
    tot = calc_transport(x)
    tot += calc_logistique(y)
    if z<tot:
        color = 'red'
    else:
        color = 'green'
    diff = z- tot
    return tot, color, diff
    
def from_name_to_indice(df, name):
    for i, value in enumerate(df.index.values):
        if value == name:
            return i

def create_chart(labels: list, values: list):
    chart = Bar("Evolution de la cotisation")
    chart.set_options(labels=labels, x_label="Année", y_label="Cotisation")
    chart.add_series("Cotisation", values)
    return chart 
    
def app():
    df= clean_pandas()
    x = df['Transport_2020']
    y = df['Logistique_2020']
    z = df['Cotis_2021']
    CC_USNEF = df['CCN_USNEF']
    for i, label in enumerate(df.index.values):
            if CC_USNEF[i] == 1:
                y[i] = y[i]*4/3
    
    topics =list(df.index.values)
    graphes = [1,2,3]
    put_select(label = 'Start Shape',name = 'start_shape', options=topics) 
    put_select(label='target shape', name='target', options=graphes)
    while True:
        new_shape = pin_wait_change(['start_shape', 'target'])
        with use_scope('shape',clear = True):
            if new_shape['name'] == 'start_shape':
                #popup(new_shape['name'])
                pin.start_shape = new_shape['value']
                indice = from_name_to_indice(df,new_shape['value'])
            else:
                pin.target = new_shape['value']
            
            labels = ['année 2021', 'scénario 1']
            values = [z[indice], calc_new_cotis(x[indice], y[indice], z[indice])[0]]
            chart = create_chart(labels, values)
            put_html(chart.render_notebook())
#    indice = from_name_to_indice(df,shape)
#    labels = ['Année 2021', 'Scénario 1']
#    values = [z[indice], calc_new_cotis(x[indice], y[indice], z[indice])[0]]
#    chart = create_chart(labels, values)
#    put_html(chart.render_notebook())

if __name__ == '__main__':
    start_server(app, debug=True, port='8080')