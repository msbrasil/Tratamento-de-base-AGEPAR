# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 11:36:05 2020

@author: Cecil Skaleski
"""
import pandas as pd
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 200)
pd.set_option('display.width', 1000)

def dados_planilha(excel_dataframe, verbose):
    dfs = excel_dataframe
    a = dfs.keys()
    if str(type(a)) == "<class 'odict_keys'>":
        #Varias planilhas
        a = list(dfs.keys())
        abas = []
        n = []
        linhas = []
        colunas = []
        for i in range(len(a)):
            abas.append(a[i])
            n.append(i)
            linhas.append(len(dfs[a[i]].index))
            colunas.append(len(dfs[a[i]].columns))
        planilhas = pd.DataFrame({'planilha': abas, 'posição': n, 'linhas': linhas, 'colunas': colunas})
        if verbose == 1:
            print("")
            print(planilhas)
    else:
        #Uma unica planilha
        print(" ")
        print("Workbook de planilha única")
        print(" ")
        planilhas = pd.DataFrame({'colunas': list(a)})
        if verbose == 1:
            print("Colunas: ")
            print(" ")
            print(planilhas)

    return (planilhas)
