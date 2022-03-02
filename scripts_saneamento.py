# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 14:43:49 2020

@author: Cecil Skaleski
@author: Emerson Hochsteiner
"""
#___________________________________________________________________________
# Funções desenvolvidas para o banco de dados de Saneamento (BAR) - AGEPAR
# Versão: 1.0
# 8 Scripts:
# consolida_dados, filtra_ativos, valor_medio, opcoes_colunas, verifica_valor, 
# agrupa, ordena, filtra_colunas, lista_colunas
# última atualização: 16/12/2020 por Cecil Skaleski 
# versão: 3.7
# 61 scripts
#___________________________________________________________________________

import pandas as pd
import numpy as np
from dados_planilha import dados_planilha
import pyxlsb
import xlsxwriter
import os 
import glob
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
from datetime import datetime

np.set_printoptions(linewidth=np.inf)
pd.set_option('display.max_columns', 25)
pd.set_option('display.max_rows', 450)
pd.set_option('display.width', 1000)
pd.set_option("display.precision", 3)
# Don't wrap repr(DataFrame) across additional lines
pd.set_option("display.expand_frame_repr", False)

def formats1(x):
    return ('{:,.2f}'.format(x)).replace(",", "~").replace(".", ",").replace("~", ".")

def formats2(x):
    return ('R${:,.2f}'.format(x)).replace(",", "~").replace(".", ",").replace("~", ".")

def formats3(x):
    return "{:.2f}%".format(x*100)

def formats4(x):
    return (format(x)).replace(",", "~").replace(".", ",").replace("~", ".")

def formats5(x):
    return (format(x)).replace(",", ".")

def formats6(x):
    return (format(x)).replace(".", ",")

def arred2(x):
    #Arredonda o valor para duas casas decimais
    res = round(x, 2)
    return res

def carrega_excel(path):
    #Carrega dados em formato excel
    df_data = pd.read_excel(path, header=[0], dtype=object, engine='openpyxl').dropna(axis=1, how="all")
    df_data.reset_index(inplace=True, drop=True)
    return df_data

def lookup(df_base, df_tab, col_conect):
    #Faz a lookup table entre os dataframes e adiciona as colunas da tabela no dataframe de base utilizando o nome da coluna de referencia indicada
    lista_base = df_base.loc[:, col_conect]
    cols_tab = df_tab.columns
    cols_add = [x for x in cols_tab if x != col_conect]
    #Adiciona as novas colunas ao dataframe de base
    for i in cols_add:
        df_base[i] = ''
    #Faz a correspondencia de valores para cada elemento
    for i in lista_base:
        mask_add = (df_tab.loc[:, col_conect] == i)
        mask_base = (df_base.loc[:, col_conect] == i)
        #Altera os campos especificados (utiliza o primeiro resultado encontrado)
        for j in cols_add:
            aux = df_tab.loc[mask_add, j]
            if len(aux) > 0:
                df_base.loc[mask_base, j] = aux.head(1).iloc[0]
    return df_base

#__________________________________________________Script 1__________________________________________________
def consolida_dados(pasta_raiz, extensao_arquivo, df_colunas_ref, altera_cabecalho):
    #Consolida os vários arquivos de banco de dados em um único e salva na raiz
    #Utilizar o dataframe com os cabeçalhos de referencia da SETAPE, importados utilizando o script importa_colunas
    #altera_cabecalho = 1: altera os cabeçalhos conforme o dataframe passado no argumento da função
    #altera_cabecalho = 0: não altera os cabeçalhos (modo report)
    #Exemplo de pasta raiz: pasta_raiz = 'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE'
    #Exemplo de formato: 'xlsb' (Por enquanto esta opção é manual, alterar linha 65 e dependencias)
    
    #Verifica qual é o sistema operacional
    sistema_op = os.name
    if sistema_op == 'nt':
        #Windows:
            formato = '\*.' + extensao_arquivo
    else:
        #Linux:
            formato = '/*.' + extensao_arquivo    
    
    #Lista as demais pastas do diretório
    lista_dir = [x[0] for x in os.walk(os.path.expanduser(pasta_raiz))]
    if len(lista_dir) > 1:
        lista_dir = sorted(lista_dir[1:len(lista_dir)])
    
    arquivos = []
    pastas = 0
    linhas = 0
    colunas = 0
    pontos = 0
    relatorio_elegibilidade = []
    relatorio_onerosidade = []
    relatorio_arquivos = []
    all_data = pd.DataFrame([])
    dep_anterior = 0
    #Roda para cada pasta:
    for k in lista_dir:
        pastas = pastas + 1
        aux_arquivos = 0
        #Print o nome de cada arquivo .xlsb encontrado em cada pasta do diretorio raiz
        for i in glob.glob(os.path.expanduser(k + formato)):
            arquivos.append(i)
            aux_arquivos = aux_arquivos + 1
            print(" ")
            print("___________________________________________________________________________________________________")
            print("Analisando o arquivo: " + os.path.basename(i))
            print("Pasta " + str(pastas) + " de " + str(len(lista_dir)) + " (" + os.path.basename(k) + ")")
            print("Arquivo " + str(aux_arquivos) + " de " + str(len(glob.glob(k + formato))))
        
            file_name = i
            
            print("Importando o arquivo...")
            
            #Importa arquivo (alterar a engine e comando de importação para outros formatos)
            if extensao_arquivo == 'pyxlsb':
                dfs = pd.read_excel(file_name, sheet_name=0, skiprows=[0], engine='pyxlsb')
            if extensao_arquivo == 'txt':
                dfs = pd.read_csv(file_name, sep=";", header=[0], engine='python')
            if extensao_arquivo == 'xlsx':
                dfs = pd.read_excel(file_name, sheet_name=0)
                

            #Contabiliza o total de processamento
            linhas = linhas + len(dfs.index)
            colunas = colunas + len(dfs.columns)
            pontos = pontos + linhas*colunas
            
            #Apresenta as informações gerais do arquivo importado
            inf = dados_planilha(dfs, 0)
            
            #Lista os tipos de ativos
            #dfs[inf['colunas'][34]]
            
            #Trabalha com a aba que contem os dados
            #dados = dfs['Base de Dados']
            #dados = dfs   
    #____________________________________________________________________________________________ 
            #Escolhe o fator de agrupamento pelo índice da coluna na matriz de dados: (Fonte: arquivos SETAPE 1ª RTP)
            #19 SERVIÇO PRESTADO (DESCRIÇÃO)
            #22 - QUANTIDADE
            #31 - Valor Residual
            #34 - Tipo de Ativo
            #41 - DESCRIÇÃO CONFORME LEVANTAMENTO FÍSICO
            #43 - Elegibilidade (ELEGÍVEIS / NÃO ELEGÍVEIS / ELEGÍVEIS-RO)
            #45 - Onerosidade (ONEROSOS / NÃO ONEROSOS)
            #46 - SITUAÇÃO DO INVENTÁRIO (CONCILIADO / SOBRA FÍSICA / SOBRA CONTÁBIL)
            #62 - VNR
            #70 - DEPRECIAÇÃO ACUMULADA REGULATÓRIA  (R$)
            #72 - VMU
            #77 - Vida útil regulatória remanescente
            #81 - VALOR ATUALIZADO POR CCV
            #86 - OBSERVAÇÃO - CONTA CONTÁBIL
     
            #Tratamento inicial dos dados
            print(" ")
            print("Dados importados com sucesso!")
            print("Pré processando os dados...")
            #Substitui os espaços vazios (NaN) das demais colunas numericas pelo valor 0:
            #for j in inf['colunas']:
                #if is_numeric_dtype(dados[j]):
                    #dados[j] = dados[j].replace(np.nan, 0, regex=True)
            #Substitui os zeros da coluna QUANTIDADE pelo valor unitario
            #dados[inf['colunas'][22]] = dados[inf['colunas'][22]].replace(0, 1, regex=True)
                
            #Substitui os espaços vazios (NaN) do dataframe pela string 'Campo vazio'
            #dados = dados.replace(np.nan, 'Campo vazio', regex=True)
            
            print(str(len(arquivos)) + " Dataframes processados")
            print("Linhas processadas: " + str(len(dfs.index)))
            
            #Substitui os cabeçalhos do arquivo importado pelos cabeçalhos de referencia do sumario executivo da SETAPE
            if altera_cabecalho == 1:
                for t in range(0, len(df_colunas_ref)):
                    dfs.rename(columns={dfs.columns[t]: df_colunas_ref['Nome'][t]}, inplace = True)
            
            #Concatena os multiplos dataframes em um único dataframe
            all_data = all_data.append(dfs, ignore_index=True)
            
            #Verifica se as colunas estão compatíveis
            df_lista_colunas = lista_colunas(dfs)
            res_colunas = verifica_colunas(df_lista_colunas, df_colunas_ref)
            res_colunas.columns = ['REF', os.path.basename(i)]
            
            print("Linhas armazenadas: " + str(len(all_data.index)))
            print("")
                        
            dep_nova = all_data.iloc[:,70].sum()
            print("Soma da depreciação acumulada: " + str(dep_nova))
            print("")
            if dep_nova == dep_anterior:
                print("Erro na depreciação!")
            dep_anterior = dep_nova*1
            
            print("")
            print('___________________________________________________')
            print(res_colunas)
            print('___________________________________________________')
            print("")            
            #Guarda as opções de elegibilidade e onerosidade disponíveis no dataframe
            aux_eleg = list(dfs[inf['colunas'][43]].unique())
            #aux_eleg.sort()
            aux_oner = list(dfs[inf['colunas'][45]].unique())
            #aux_oner.sort()
            
            #Anota as opções de cada coluna para verificação ao final
            relatorio_arquivos.append(os.path.basename(i))
            relatorio_elegibilidade.append(aux_eleg)
            relatorio_onerosidade.append(aux_oner)
            print("Tags elegibilidade existentes: " + str(aux_eleg))
            print("Tags onerosidade existentes: " + str(aux_oner))
            
    #Monta o dataframe de check de consistência da filtragem
    relatorio = pd.DataFrame({'Tags elegibilidade': relatorio_elegibilidade, 'Tags onerosidade':  relatorio_onerosidade})
            
    print(" ")
    #Resumo do processamento   
    print("____________________________________RESUMO____________________________________")
    print("Arquivos analisados: " + str(len(arquivos)))
    print("Linhas processadas: " + str(linhas))
    print("Colunas processadas: " + str(colunas))
    print("Pontos processados: " + str(pontos))
    print(" ")
    
    print("")
    print("Check de critérios de elegibilidade e onerosidade disponíveis no banco de dados:")
    print(relatorio)
    print(" ")
    print("Lista de arquivos processados: ")
    for i in arquivos:
        print(i)
    
    #Salva o DataFrame tratado como hdf5
    print(" ")
    print("Tamanho do DataFrame final: " + str(len(all_data)))
    print(" ")
    print("Salvando o banco de dados consolidado...")
    save_file_name = pasta_raiz + '\DB_consolidado.h5'
    all_data.to_hdf(save_file_name, key='all_data', mode='w')
    print("Arquivo salvo no seguinte local: ")
    print(save_file_name)
    
    return all_data
#--------------------------------------------------Script 1--------------------------------------------------


#__________________________________________________Script 2__________________________________________________
def filtra_ativos(database, lista_categorias_ativos, lista_colunas_filtro, indice_coluna_cat):
  
    #filtra o banco de dados selecionando todos os ativos da lista de categorias e retornando as colunas selecionadas
   
    #Carrega lista com as categorias (descrição) de interesse (Exemplo de sintaxe)
    #file_cat = 'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE\lista_categorias_all.txt'
    #df_cat = pd.read_csv(file_cat, sep=';', header=None)[0].to_list()
    df_cat = lista_categorias_ativos
    print(" ")
    print("Categorias de ativos selecionadas: " + str(len(df_cat)))
    
    #Carrega lista com os índices (colunas) de interesse
    #file_indices = 'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE\lista_indices.txt'
    #df_indices = pd.read_csv(file_indices, header=None)[0].to_list()
    df_indices = lista_colunas_filtro
    print("Colunas selecionadas: " + str(len(df_indices)))
    
    dados = database.copy()
    #Lista de colunas existente no banco de dados
    inf = lista_colunas(dados)
    
    #Constroi o filtro de colunas dinamicamente
    filtro_colunas = 'dados[['
    for i in df_indices:
        if len(df_indices) > 1 and i != df_indices[len(df_indices)-1]:
            filtro_colunas = filtro_colunas + "inf['Nome'][" + str(i) + '], '
        else:
            filtro_colunas = filtro_colunas + "inf['Nome'][" + str(i) + ']'
    filtro_colunas = filtro_colunas + ']]'
    
    #Filtra o dataframe com as colunas de interesse
    print("Filtrando colunas...")
    dados = eval(filtro_colunas)
    
    #Nome da coluna que contém as categorias de ativos
    cat_filter = inf['Nome'][indice_coluna_cat]
    linha = 0
    print("Filtrando categorias...")
    for r in df_cat:
        #Verifica se é a primeira execução do loop
        if linha == 0:
            #Monta o dataframe inicial cujas categorias do banco de dados são iguais às desejadas
            df_filtrado = dados.loc[dados[cat_filter] == r]
        else:
            #Faz um append no dataframe inicial
            aux_filtro = dados.loc[dados[cat_filter] == r]
            if len(aux_filtro) != 0:
                df_filtrado = df_filtrado.append(aux_filtro)
        linha = linha + 1
    
    return df_filtrado
#--------------------------------------------------Script 2--------------------------------------------------


#__________________________________________________Script 3__________________________________________________
def valor_medio(database, indice_coluna_valor, indice_coluna_quantidade):
    #Calcula o valor médio do parâmetro selecionado para cada ativo e insere na coluna imediatamente após a coluna com o parâmetro calculado
    
    #Lista de colunas existente no banco de dados
    inf = lista_colunas(database)
    
    aux = database.copy()
    #Calcula o parÂmetro medio por ativo
    aux.insert(aux.columns.get_loc(inf['Nome'][indice_coluna_valor])+1, inf['Nome'][indice_coluna_valor] + ' MÉDIO/ATIVO', (aux[inf['Nome'][indice_coluna_valor]]/aux[inf['Nome'][indice_coluna_quantidade]]).to_list())

    return aux
#--------------------------------------------------Script 3--------------------------------------------------


#__________________________________________________Script 4__________________________________________________
def opcoes_colunas(database, limite_min, limite_max):
    #Retorna a lista de opções para cada coluna, respeitando o limite de quantidade máxima de itens únicos encontrados
    
    #Guarda o nome de cada coluna do dataframe
    colunas = database.columns.to_list()
    
    
    for i in colunas:
        i_col = colunas.index(i)
        #Conta a frequência de cada opção e apresenta o percentual ao lado
        aux = database.groupby([i]).size().reset_index(name='qtde itens')
        aux['%'] = aux['qtde itens']/aux['qtde itens'].sum()*100
        
        #Ordena pelo menor percentual (maior probabilidade de ser erro)
        aux = aux.sort_values('%', ascending=False).reset_index(drop=True)
        aux['%'] = aux['%'].apply(formats1)
        if len(aux) >= limite_min and len(aux) <= limite_max:
            print("")
            print("________________________________________ índice coluna: " + str(i_col) + " ________________________________________")
            print(aux)
    
    return 
#--------------------------------------------------Script 4--------------------------------------------------


#__________________________________________________Script 5__________________________________________________
def verifica_valor(database, lista_categorias, colunas_referencia):
    #Verifica quais categorias da lista possuem mais de um valor para as colunas de referencia e retorna a lista
    return lista_valor_medio
#--------------------------------------------------Script 5--------------------------------------------------


#__________________________________________________Script 6__________________________________________________
def agrupa(database, i_colunas_agrupamento, i_coluna_agregacao, ordem_decrescente, formatar):
    #Agrupa os dados por uma coluna específica e retorna as colunas selecionadas
    
    
    #Constroi o filtro de colunas de agrupamento dinamicamente
    colunas_agrupamento = '['
    for i in i_colunas_agrupamento:
        if len(i_colunas_agrupamento) > 1 and i != i_colunas_agrupamento[len(i_colunas_agrupamento)-1]:
            colunas_agrupamento = colunas_agrupamento + "database.columns[" + str(i) + '], '
        else:
            colunas_agrupamento = colunas_agrupamento + "database.columns[" + str(i) + ']'
    colunas_agrupamento = colunas_agrupamento + ']'
    
    #Constroi o comando para agrupamento:
    comando_agrup = "database.groupby(" + colunas_agrupamento + ")[database.columns[i_coluna_agregacao]].sum().reset_index(name=database.columns[i_coluna_agregacao])"
    df_agrupado = eval(comando_agrup)
    
    if ordem_decrescente == 1:
        df_agrupado = df_agrupado.sort_values(database.columns[i_coluna_agregacao], ascending=False).reset_index(drop=True)
  
    if formatar == 1:
        #Formata como dinheiro
        df_agrupado.iloc[:,len(df_agrupado.columns)-1] = df_agrupado.iloc[:,len(df_agrupado.columns)-1].map(formats2)
    
    return df_agrupado
#--------------------------------------------------Script 6--------------------------------------------------


#__________________________________________________Script 7__________________________________________________
def ordena(database, colunas_ordenamento, ordem):
    #Ordena os dados por uma lista de colunas e ordem específica (ascendente ou descendente) 
    
    aux = database.copy()
    
    #Gera o vetor de ordenamento
    colunas = aux.columns.tolist()
    colunas_ordem = []
    for i in colunas_ordenamento:
        colunas_ordem.append(colunas[i])
    
    #Converte a ordem para booleano
    if ordem == 'ascendente':
        ordem = True
    else:
        ordem = False
        
    #ordena o dataframe
    aux = aux.sort_values(colunas_ordem, ascending=ordem)
    
    return aux
#--------------------------------------------------Script 7--------------------------------------------------


#__________________________________________________Script 8__________________________________________________
def filtra_colunas(database, lista_indices_colunas):
    #Filtra o dataframe apresentando somente a lista de colunas selecionadas
    
    df_indices = lista_indices_colunas 
    
    colunas = lista_colunas(database)
    #filtra o banco de dados por uma lista de categorias
    filtro_colunas = 'database[['
    
    #Constroi o filtro de colunas dinamicamente
    for i in df_indices:
        if len(df_indices) > 1 and i != df_indices[len(df_indices)-1]:
            filtro_colunas = filtro_colunas + "colunas['Nome'][" + str(i) + '], '
        else:
            filtro_colunas = filtro_colunas + "colunas['Nome'][" + str(i) + ']'
    filtro_colunas = filtro_colunas + ']]'
    
    aux = eval(filtro_colunas)
    
    return aux
#--------------------------------------------------Script 8--------------------------------------------------


#__________________________________________________Script 9__________________________________________________
def lista_colunas_excel(database, verbose):
    #Retorna o dataframe com a lista de colunas
    #Verbose = 1: lista as colunas
    #Verbose = 0: apenas retorna o dataframe, sem printar
    dfs = database.copy()
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
#--------------------------------------------------Script 9--------------------------------------------------


#__________________________________________________Script 10__________________________________________________
def calcula_vnr(database, indice_categoria, indice_VNR, indice_qtde, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o VNR
    
    #calcula_vnr(banco_elegiveis, 19, 62, 22, 0)
    
    inf = lista_colunas(database)
    f_grupo = inf['Nome'][indice_categoria]
    f_ordem = inf['Nome'][indice_VNR]
    f_qtde = inf['Nome'][indice_qtde]
    aux = database.copy()
    
    #Filtra o dataframe expurgando os ativos em que VNR é nulo
    aux = filtra_coluna(aux, indice_VNR, 0, '!=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='VNR total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['VNR médio/ativo'] = df_ordenado['VNR total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('VNR total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['VNR total'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado['VNR total [%]'] = df_ordenado['VNR total']/df_ordenado['VNR total'].sum()
    df_ordenado['VNR acumulado'] = df_ordenado['VNR total'].cumsum()/df_ordenado['VNR total'].sum()
    
    print("")
    print("VNR Total: " + str(custo_ativos))
    print("")
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['VNR total'] = df_ordenado['VNR total'].apply(formats2)
        df_ordenado['VNR médio/ativo'] = df_ordenado['VNR médio/ativo'].apply(formats2)
        df_ordenado['VNR total [%]'] = df_ordenado['VNR total [%]'].apply(formats3)
        df_ordenado['VNR acumulado'] = df_ordenado['VNR acumulado'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 10--------------------------------------------------


#__________________________________________________Script 11__________________________________________________
def calcula_ccv(database, indice_categoria, indice_CCV, indice_qtde, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o CCV
    
    #calcula_ccv(banco_eleg, 19, 81, 22, 1)
    
    inf = lista_colunas(database)
    f_grupo = inf['Nome'][indice_categoria]
    f_ordem = inf['Nome'][indice_CCV]
    f_qtde = inf['Nome'][indice_qtde]
    aux = database.copy()
    
    #Filtra o dataframe expurgando os ativos em que VNR é nulo
    aux = filtra_coluna(aux, indice_CCV, 0, '!=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='CCV total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['CCV médio/ativo'] = df_ordenado['CCV total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('CCV total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['CCV total'].sum()

    print("")
    print("CCV Total: " + str(custo_ativos))
    print("")
    
    #Calcula representatividade relativa e acumulada
    df_ordenado['CCV total [%]'] = df_ordenado['CCV total']/df_ordenado['CCV total'].sum()
    df_ordenado['CCV acumulado'] = df_ordenado['CCV total'].cumsum()/df_ordenado['CCV total'].sum()
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['CCV total'] = df_ordenado['CCV total'].apply(formats2)
        df_ordenado['CCV médio/ativo'] = df_ordenado['CCV médio/ativo'].apply(formats2)
        df_ordenado['CCV total [%]'] = df_ordenado['CCV total [%]'].apply(formats3)
        df_ordenado['CCV acumulado'] = df_ordenado['CCV acumulado'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 11--------------------------------------------------


#__________________________________________________Script 12__________________________________________________
def calcula_deprec(database, indice_categoria, indice_depreciacao, i_dep, indice_qtde, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o valor dos itens 100% depreciados
    
   #calcula_deprec(banco_eleg, 19, 70, 71, 22, 1)
   
    inf = lista_colunas(database)
    f_grupo = inf['Nome'][indice_categoria]
    f_ordem = inf['Nome'][indice_depreciacao]
    f_qtde = inf['Nome'][indice_qtde]
    aux = database.copy()
    
    #Arredonda o índice para inteiro
    #aux.iloc[:, i_dep] = aux.iloc[:, i_dep].round(decimals=0)
    #Filtra o dataframe selecionado somente os itens 100% depreciados
    aux = filtra_coluna(aux, i_dep, 99.995, '>=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='Depreciação total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['Dep média/ativo'] = df_ordenado['Depreciação total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('Depreciação total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['Depreciação total'].sum()

    print("")
    print("100% Depreciados: " + str(custo_ativos))
    print("")

    #Calcula representatividade relativa e acumulada
    df_ordenado['Dep total [%]'] = df_ordenado['Depreciação total']/df_ordenado['Depreciação total'].sum()
    df_ordenado['Dep (acumulado)'] = df_ordenado['Depreciação total'].cumsum()/df_ordenado['Depreciação total'].sum()
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['Depreciação total'] = df_ordenado['Depreciação total'].apply(formats2)
        df_ordenado['Dep média/ativo'] = df_ordenado['Dep média/ativo'].apply(formats2)
        df_ordenado['Dep total [%]'] = df_ordenado['Dep total [%]'].apply(formats3)
        df_ordenado['Dep (acumulado)'] = df_ordenado['Dep (acumulado)'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 12--------------------------------------------------


#__________________________________________________Script 13__________________________________________________
def calcula_ro(database, i_elegiveis):
    #filtra e calcula a reserva operacional móvel
    
    aux = filtra_coluna(database, i_elegiveis, 'ELEGÍVEIS-RO', '==')
    
    #Soma o VNR dos ativos de reserva operacional e o CCV
    valor_ro_bruto = aux.iloc[:,62].sum() + aux.iloc[:,81].sum()
    
    #Desconta a depreciação acumulada
    valor_ro_liq = valor_ro_bruto - aux.iloc[:, 70].sum()
    
    return aux, valor_ro_bruto, valor_ro_liq
#--------------------------------------------------Script 13--------------------------------------------------


#__________________________________________________Script 14__________________________________________________
def bar_bruta(database, i_categoria, i_qtde, i_eleg, i_VNR, i_IA, i_CCV, i_dep, i_conta_contabil, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula a bar bruta
    #Calculo conforme Nota Técnica RTP SANEPAR 09/11/2017 (pag.10)
    #BAR_bruta = SOMA(VNR x IA + CCV) - 100%_depreciado - (VNR_terrenos x IA_terrenos) - RO
    #Indice QTDE: 22
    #Indice Elegibilidade: 43
    #Indice VNR: 62
    #Indice IA: 73
    #Indice CCV: 81
    #Indice Depreciação Regulatoria %: 71
    #Indice Conta Contabil (Descrição): 140
    #bar_bruta(banco, i_categoria, 22, 43, 62, 73, 81, 71, 140, 1)
    
    aux = database.copy()
    
    #Remove os ativos baixados
    ativos, baixados = baixa_ativos(aux, i_dep)
        
    #Remove os terrenos
    ativos = filtra_coluna(ativos, i_conta_contabil, 'Terrenos', '!=')
    
    #Filtra os elegíveis (Já removendo a reserva operacional)
    ativos = filtra_coluna(ativos, i_eleg, 'ELEGÍVEIS', '==')
    
    #Remove os não onerosos
    ativos = filtra_coluna(ativos, 45, 'ONEROSOS', '==')

    #Substitui os valores de IA = 0 que eram Campo vazio por 100
    ativos = substitui_valor(ativos, i_IA, 0, 100)
    #Cria a coluna no dataframe com a conta a ser feita
    ativos.loc[:,'BAR bruta'] = ativos.iloc[:, i_VNR]*ativos.iloc[:, i_IA]/100 + ativos.iloc[:, i_CCV]

    print("")
    print('VNR x  IA sem terrenos: ' + str(formats2(ativos['BAR bruta'].sum() - ativos.iloc[:, i_CCV].sum())))
    
    BAR_bruta_total = ativos['BAR bruta'].sum()
    print("")
    print("BAR_bruta_total: " + formats2(BAR_bruta_total))
    print("")
    
    inf = lista_colunas(ativos)
    f_grupo = inf['Nome'][i_categoria]
    f_ordem = 'BAR bruta'
    f_qtde = inf['Nome'][i_qtde]
    aux = ativos*1
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='BAR bruta')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['BAR b. média/ativo'] = df_ordenado['BAR bruta']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('BAR bruta', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['BAR bruta'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado['BAR b. [%]'] = df_ordenado['BAR bruta']/df_ordenado['BAR bruta'].sum()
    df_ordenado['BAR b. acumulada'] = df_ordenado['BAR bruta'].cumsum()/df_ordenado['BAR bruta'].sum()
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['BAR bruta'] = df_ordenado['BAR bruta'].apply(formats2)
        df_ordenado['BAR b. média/ativo'] = df_ordenado['BAR b. média/ativo'].apply(formats2)
        df_ordenado['BAR b. [%]'] = df_ordenado['BAR b. [%]'].apply(formats3)
        df_ordenado['BAR b. acumulada'] = df_ordenado['BAR b. acumulada'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 14--------------------------------------------------


#__________________________________________________Script 15__________________________________________________
def bar_liquida(database, i_categoria, i_qtde, i_eleg, i_VNR, i_IA, i_CCV, i_dep, i_dep_acum, i_conta_contabil, i_VMU_IA, CG, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula a bar líquida
    #Calculo conforme Nota Técnica RTP SANEPAR 09/11/2017 (pag.11)
    #BAR_liquida = SOMA(VNR x IA + CCV) - 100%_depreciado + (VNR_terrenos x IA_terrenos) + RO - Dep_acum x IA - NO + CG
    #NO: Valor dos ativos não onerosos líquidos de depreciação;
    #CG: Capital de Giro
    #RO: Reserva Técnica Operacional Móvel
    #DepAcum.x.IA: Valor da depreciação acumulada multiplicada pelo índice de aproveitamento;
    #bar_liquida(banco, i_categoria, 55, 43, 62, 73, 81, 71, 70, 140, 79, 0, 1)
    #bar_liquida(dados_atualizados, i_categoria, 55, 43, 157, 151, 158, 149, 159, 140, 161, 0, 1)
    
    #Indice QTDE: 22
    #Indice VNR: 62
    #Indice IA: 73
    #Indice CCV: 81
    #Indice Depreciação %: 71
    #Indice Conta Contabil (Descrição): 148

    #REPRODUZ OS CALCULOS DA BAR BRUTA SEM EXCLUIR OS TERRENOS
    aux = database.copy()
    
    #Remove os ativos baixados
    ativos, baixados = baixa_ativos(aux, i_dep)
    
    #Remove os não onerosos
    ativos = filtra_coluna(ativos, 45, 'ONEROSOS', '==')
    
    #Remove não elegíveis e campos vazios
    ativos = filtra_coluna(ativos, 43, 'NÃO ELEGÍVEIS', '!=')
    ativos = filtra_coluna(ativos, 43, 'Campo vazio', '!=')
        
    #Cria duas mascaras para os RO
    mask_elegiveis_ro = (ativos.iloc[:, 43] == 'ELEGÍVEIS-RO')
    mask_elegiveis = (ativos.iloc[:, 43] == 'ELEGÍVEIS')
   
    #Substitui os valores de IA = 0 que eram Campo vazio por 100
    ativos = substitui_valor(ativos, i_IA, 0, 100)
    #Cria um dataframe só com os valores elegiveis
    ativos_valid = ativos[mask_elegiveis]
    #Cria a coluna no dataframe com a conta a ser feita
    ativos.loc[:,'BAR líquida'] = 0
    #Refaz a conta nas linhas dos elegiveis-RO
    ativos.loc[mask_elegiveis, 'BAR líquida'] = ativos_valid.iloc[:, i_VNR]*ativos_valid.iloc[:, i_IA]/100 + ativos_valid.iloc[:, i_CCV] - ativos_valid.iloc[:, i_dep_acum]*ativos_valid.iloc[:, i_IA]/100
    print("")
    print("VNRxIA + CCV: " + str(formats2((ativos_valid.iloc[:, i_VNR]*ativos_valid.iloc[:, i_IA]/100 + ativos_valid.iloc[:, i_CCV]).sum())))
    print("DepxIA: " + str(formats2((ativos_valid.iloc[:, i_dep_acum]*ativos_valid.iloc[:, i_IA]/100).sum())))
    print("VNRxIA + CCV - DepxIA: " + str(formats2((ativos_valid.iloc[:, i_VNR]*ativos_valid.iloc[:, i_IA]/100 + ativos_valid.iloc[:, i_CCV] - ativos_valid.iloc[:, i_dep_acum]*ativos_valid.iloc[:, i_IA]/100).sum())))
    #Cria um dataframe só com os valores elegiveis-ro
    ativos_valid = ativos[mask_elegiveis_ro]    
    #Refaz a conta nas linhas dos elegiveis-RO
    ativos.loc[mask_elegiveis_ro, 'BAR líquida'] = ativos_valid.iloc[:, i_VMU_IA]
    print("RO: " + str(formats2((ativos_valid.iloc[:, i_VMU_IA]).sum())))
    
    BAR_liquida_total = ativos['BAR líquida'].sum()
    print("")
    print("BAR_liquida_total: " + formats2(BAR_liquida_total - CG))
    print("")
    
    inf = lista_colunas(ativos)
    f_grupo = inf['Nome'][i_categoria]
    f_ordem = 'BAR líquida'
    f_qtde = inf['Nome'][i_qtde]
    aux = ativos*1
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='BAR liquida')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['BAR l. média/ativo'] = df_ordenado['BAR liquida']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('BAR liquida', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['BAR liquida'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado['BAR l. [%]'] = df_ordenado['BAR liquida']/df_ordenado['BAR liquida'].sum()
    df_ordenado['BAR l. acumulada'] = df_ordenado['BAR liquida'].cumsum()/df_ordenado['BAR liquida'].sum()
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['BAR liquida'] = df_ordenado['BAR liquida'].apply(formats2)
        df_ordenado['BAR l. média/ativo'] = df_ordenado['BAR l. média/ativo'].apply(formats2)
        df_ordenado['BAR l. [%]'] = df_ordenado['BAR l. [%]'].apply(formats3)
        df_ordenado['BAR l. acumulada'] = df_ordenado['BAR l. acumulada'].apply(formats3)
    
    return df_ordenado    
#--------------------------------------------------Script 15--------------------------------------------------


#__________________________________________________Script 16__________________________________________________
def atualiza_ativos(database, indices, colunas):
    #Atualiza as colunas especificas do banco de dados com base na matriz de indices economicos fornecida
    #Exemplo de matriz de indices: IGPM - Data
    return df_bar_atualizada
#--------------------------------------------------Script 16--------------------------------------------------


#__________________________________________________Script 17__________________________________________________
def atualiza_ia(database, indices):
    #Atualiza os indices de aproveitamento do banco de dados com base na matriz de indices
    #Exemplo de matriz de indices: Descrição do ativo - IA
    return df_bar_atualizada_ia
#--------------------------------------------------Script 17--------------------------------------------------


#__________________________________________________Script 18__________________________________________________
def remove_espacos(database):
    #Remove os espaços em branco do início e do final de todos os campos do dataframe que contenham strings
    #Retorna o relatório das strings alteradas, por coluna e quantidade
    
    #Guarda o nome de cada coluna do dataframe
    colunas = database.columns.to_list()
    
    aux = database.copy()
    #Analisa o tipo de dado em cada coluna
    #Substitui os espaços vazios (NaN) das demais colunas numericas pelo valor 0:
    for i in colunas:
        if is_string_dtype(aux[i]):
            aux[i] = aux[i].str.strip()
    
    return aux
#--------------------------------------------------Script 18--------------------------------------------------


#__________________________________________________Script 19__________________________________________________
def importa_dados(path):
    #importa os dados de um arquivo hdf5
    
    #'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE\DB_consolidado.h5'
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\LAUDO SETAPE 2015\DB_consolidado_24nov20_R5.h5'
    #path = 'C:\Teste\DB_atualizado_sanepar.h5'
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\LAUDO SETAPE 2015\DB_atualizado_12_2021_2aRTP\DB_atualizado_agepar.h5'
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\BAR_incremental.h5'
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\BAR_incremental_filtrada.h5'
    
    dados = pd.read_hdf(os.path.expanduser(path))

    return dados
#--------------------------------------------------Script 19--------------------------------------------------


#__________________________________________________Script 20__________________________________________________
def trata_dados(database):
    #Tratamento inicial dos dados
    #Guarda o nome de cada coluna do dataframe
    colunas = database.columns.to_list()
    
    aux = database.copy()
    #Substitui os espaços vazios (NaN) das demais colunas numericas pelo valor 0:
    for j in colunas:
        if is_numeric_dtype(aux[j]):
            aux[j] = aux[j].replace(np.nan, 0, regex=True)
            
    #Substitui os zeros da coluna QUANTIDADE pelo valor unitario
    aux[colunas[22]] = aux[colunas[22]].replace(0, 1, regex=True)
   
    #Substitui os espaços vazios (NaN) do dataframe pela string 'Campo vazio'
    aux = aux.replace(np.nan, 'Campo vazio', regex=True)
    
    #Remove o excesso de espaços nos cabeçalhos
    aux.columns = aux.columns.str.replace(r'\s\s', ' ')
    
    #Converte os formatos de data para time stamps do pandas
    #Colunas 24, 25, 32, 49, 65, 109, 110 (64 está como string)
    aux_col = [24, 25, 32, 49, 64, 65, 109, 110]
    for i in aux_col:
        #Remove a string:
        aux.iloc[:, i] = aux.iloc[:, i].replace('Campo vazio', 0, regex=True)
        #Converte para timestamp
        aux.iloc[:, i] = aux.iloc[:, i].apply(transforma_data)

        #Filtra elementos que não sejam strings
        #mask = (aux.iloc[:, i].apply(type) != str)
        #Remove a string:
        #aux.iloc[:, i] = aux.iloc[:, i].replace('Campo vazio', 99999, regex=True)
        
        #Converte para um formato de data mais simples:
        aux.iloc[:, i] = pd.to_datetime(aux.iloc[:, i])
        #aux.iloc[:, i] = data_aux
        #Converte para numero do mês e ano:
        aux.iloc[:, i] = aux.iloc[:, i].apply(lambda x: x.strftime('%m/%Y'))
        #Substitui os marcadores de data do dataframe pela string 'Campo vazio'
        aux.iloc[:, i] = aux.iloc[:, i].replace('01/2099', 'Campo vazio', regex=True)

    #Remove os espaços dos cabeçalhos
    aux = remove_espacos(aux)
    
    return aux
#--------------------------------------------------Script 20--------------------------------------------------


#__________________________________________________Script 21__________________________________________________
def filtra_coluna(database, indice_coluna, valor, condicao):
    #filtra o banco de dados por um indice de coluna
    
    #condição: '>', '<', '!=' ou '=='
    #Guarda o nome de cada coluna do dataframe
    colunas = database.columns.to_list()
    
    aux = eval('database.loc[database[colunas[indice_coluna]]' + condicao + 'valor]')
    
    return aux
#--------------------------------------------------Script 21--------------------------------------------------


#__________________________________________________Script 22__________________________________________________
def opcoes_coluna(database, indice):
    #Retorna as opções disponíveis em uma coluna especifica

    #Guarda o nome de cada coluna do dataframe
    colunas = database.columns.to_list()
    
    #Conta a frequência de cada opção e apresenta o percentual ao lado
    aux = database.groupby([colunas[indice]]).size().reset_index(name='qtde itens')
    aux['%'] = aux['qtde itens']/aux['qtde itens'].sum()*100
    
    #Ordena pelo menor percentual (maior probabilidade de ser erro)
    aux = aux.sort_values('%', ascending=False).reset_index(drop=True)
    aux['%'] = aux['%'].apply(formats1)
   
    return aux
#--------------------------------------------------Script 22--------------------------------------------------


#__________________________________________________Script 23__________________________________________________
def lista_colunas(database):
    #Lista as colunas do banco de dados
    
    colunas = pd.DataFrame(database.columns.to_list())
    colunas.columns = ['Nome']
    
    return colunas
#--------------------------------------------------Script 23--------------------------------------------------

            
#__________________________________________________Script 24__________________________________________________
def salva_dados(database, path, nome_arquivo):
    #Salva o banco de dados em formato hdf5 no local especificado
    local = path + '\\' + nome_arquivo + '.h5'
    database.to_hdf(local, key='database', mode='w')
    
    #CSV
    #database.to_csv(file_name, sep=';', encoding='utf-8', compression='gzip')
    
    return
#--------------------------------------------------Script 24--------------------------------------------------


#__________________________________________________Script 25__________________________________________________
def verifica_vnr_medio():
    #Verifica quais ativos possuem mais de um VNR médio
    #Calcula a média ponderada do VNR médio de cada ativo, estabelecendo a referência
    #Multiplica o VNR médio pela quantidade
    total = []
    for i in range(0, len(opcoes_coluna(banco3, 0))):
        a = filtra_ativos(banco3, [opcoes_coluna(banco3, 0).iloc[i,0]], [0, 1, 2, 3], 0)
        print("")
        print(opcoes_coluna(banco3, 0).iloc[i,0])
        print("")
        a = filtra_coluna(a, 2, 'Campo vazio', '!=')
        #a.drop_duplicates(subset=[a.columns[0], a.columns[2], a.columns[3]], keep='first', inplace=False)
        a = a.drop_duplicates(subset=[a.columns[3]], keep='first', inplace=False)
        a = a.sort_values(a.columns[3], ascending=False).reset_index(drop=True)
        a = filtra_coluna(a, 3, 0, '!=')
        if len(a) > 1:
            variacao = ([[a.iloc[0, 2], a.iloc[0, 3]]])
            variacao.append([a.iloc[len(a)-1, 2], a.iloc[len(a)-1, 3]])
            variacao.append(['Delta', round((variacao[0][1]-variacao[1][1])/variacao[0][1]*100,2)])
            var = pd.DataFrame(variacao)
            var.columns = ['UR', 'VNR MÉDIO/ATIVO']
            total.append([opcoes_coluna(banco3, 0).iloc[i,0], variacao[0][0], round((variacao[0][1]-variacao[1][1])/variacao[0][1]*100,2)])
            
    df_total = pd.DataFrame(total)
    df_total.columns = ['TIPO DO ATIVO', 'REGIONAL', 'DELTA VNR [%]']
    df_total = df_total.sort_values('DELTA VNR [%]', ascending=False).reset_index(drop=True)
    df_total = filtra_coluna(df_total, 2, 0, '!=')
    print(df_total)
    
    #Salva planilha analisada
    nome_arquivo = 'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE\lista_vnr_medio.xlsx'
    df_total.to_excel(nome_arquivo, engine='xlsxwriter')
    
#--------------------------------------------------Script 25--------------------------------------------------


#__________________________________________________Script 26__________________________________________________
def importa_plano_contas(path):
    #Importa o plano de contas em formato excel
    
    #Importa arquivo excel (alterar a engine e comando de importação para ooutros formatos)
    dfs = pd.read_excel(path, sheet_name=0)
    #path = 'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE\Plano_de_contas_SANEPAR_out_2020.xlsx'
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\Planilhas_SETAPE\Plano_de_contas_SANEPAR_out_2020.xlsx'
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\clusterizacao.xlsx'
    
    #Remove as linhas com valores NaN
    dfs = dfs.dropna()
    
    #Remove os espaços em branco
    dfs = remove_espacos(dfs)
    
    return dfs
#--------------------------------------------------Script 26--------------------------------------------------


#__________________________________________________Script 27__________________________________________________
def insere_plano_contas(database, indice_conta_contabil, df_plano_contas, nome_plano):
    #Insere o plano de contas no final do dataframe
    # Indice conta contabil: 86
    
    aux = database.copy()
    tamanho = len(aux.columns)
    colunas = lista_colunas(aux)
   
    #Cria a nova coluna no final do dataframe copiando a coluna com os codigos contabeis
    aux[nome_plano] = aux.iloc[:, indice_conta_contabil]
    
    codigos_plano_conta = opcoes_coluna(df_plano_contas, 0).iloc[:,0].to_list()
    codigos_contabil = opcoes_coluna(aux, indice_conta_contabil).iloc[:,0].to_list()
    
    #Varre o dataframe na coluna indicada, alimentando a coluna do plano de contas fazendo a correspondencia com a tabela do plano de contas
    for i in codigos_contabil:
        #Verifica se o código existe na matriz de plano de contas
        if i in codigos_plano_conta:
            descricao_plano_contas = df_plano_contas[df_plano_contas['Conta']==i]['Descrição'].iloc[0]
            #Substitui o codigo contabil da coluna pela descrição do plano de contas
            aux[nome_plano] = aux[nome_plano].replace(i, descricao_plano_contas, regex=True)
        else:
            aux[nome_plano] = aux[nome_plano].replace(i, 'Código não encontrado', regex=True)
 
    return aux
#--------------------------------------------------Script 27--------------------------------------------------


#__________________________________________________Script 28__________________________________________________
def baixa_ativos(database, indice_dep_acum):
    #Remove do dataframe os ativos 100% depreciados e guarda em dataframe a parte (criterio de 99.999407% de depreciação acumulada por ser o parametro que se aproximou mais do valor na Nota Tecnica Agepar RTP de 09/11/2017 pag.11)
    
    aux = database.copy()
    
    #Filtra o dataframe selecionando somente as linhas em que a depreciação acumulada é inferior a 100%
    #ativos = aux[aux.iloc[:,indice_dep_acum] <= 99.999407]
    ativos = aux[aux.iloc[:,indice_dep_acum] < 99.995]

    baixados = aux[aux.iloc[:,indice_dep_acum] >= 99.995]
    
    return ativos, baixados
#--------------------------------------------------Script 28--------------------------------------------------


#__________________________________________________Script 29__________________________________________________
def substitui_valor(database, indice_coluna, valor_original, valor_novo):
    #Na coluna indicada, troca todos os valores originais pelos novos
    
    aux = database.copy()
    
    #Substitui os zeros da coluna QUANTIDADE pelo valor unitario
    aux.iloc[:,indice_coluna] = aux.iloc[:,indice_coluna].replace(valor_original, valor_novo, regex=False)
    
    return aux
#--------------------------------------------------Script 29--------------------------------------------------


#__________________________________________________Script 30__________________________________________________
def vnr_ia(database, i_categoria, i_VNR, i_IA, i_qtde, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o VNR x IA
    #vnr_ia(banco_eleg, 19, 62, 73, 22, 1)
    
    aux = database.copy()
    
    #Filtra o dataframe expurgando os ativos em que VNR é nulo
    ativos = filtra_coluna(aux, i_VNR, 0, '!=')
    
    #Calcula o VNR x IA
    #Multiplica VNR pelo IA:
    #Cria uma mascara no dataframe para os valores de IA diferentes de 0 (estes valores não devem ser multiplicados pois não se aplicam às categorias de ativos correspondentes)
    mask = (ativos.iloc[:,i_IA] != 0)
    #Cria um dataframe só com os valores validos para a multiplicação
    ativos_valid = ativos[mask]
    #Cria a coluna no dataframe com a conta a ser feita (sem multiplicar pelo IA)
    ativos = ativos*1
    ativos.loc[:,'VNR x IA'] = ativos.iloc[:, i_VNR]
    #Refaz a conta nas linhas em que o indice de aproveitamento não é nulo:
    ativos.loc[mask, 'VNR x IA'] = ativos_valid.iloc[:, i_VNR]*ativos_valid.iloc[:, i_IA]/100

    vnr_ia = ativos['VNR x IA'].sum()
    print("")
    print("VNR x IA: " + formats2(vnr_ia))
    print("")
    
    inf = lista_colunas(ativos)
    f_grupo = inf['Nome'][i_categoria]
    f_ordem = 'VNR x IA'
    f_qtde = inf['Nome'][i_qtde]
    aux = ativos*1
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='VNR x IA total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado.loc[:,'VNR x IA médio/ativo'] = df_ordenado['VNR x IA total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('VNR x IA total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado.loc[:,'Qtde ativos'].sum()
    custo_ativos = df_ordenado.loc[:,'VNR x IA total'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado.loc[:,'VNR x IA total [%]'] = df_ordenado['VNR x IA total']/df_ordenado['VNR x IA total'].sum()
    df_ordenado.loc[:,'VNR x IA acumulado'] = df_ordenado['VNR x IA total'].cumsum()/df_ordenado['VNR x IA total'].sum()
    
    print("")
    print("VNR x IA Total: " + str(custo_ativos))
    print("")
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado.loc[:,'VNR x IA total'] = df_ordenado['VNR x IA total'].apply(formats2)
        df_ordenado.loc[:,'VNR x IA médio/ativo'] = df_ordenado['VNR x IA médio/ativo'].apply(formats2)
        df_ordenado.loc[:,'VNR x IA total [%]'] = df_ordenado['VNR x IA total [%]'].apply(formats3)
        df_ordenado.loc[:,'VNR x IA acumulado'] = df_ordenado['VNR x IA acumulado'].apply(formats3)
    
    return df_ordenado

#--------------------------------------------------Script 30--------------------------------------------------


#__________________________________________________Script 31__________________________________________________
def vnr_ia_terrenos(database, i_categoria, i_VNR, i_IA, i_qtde, i_conta_contabil, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o VNR x IA
    
    #vnr_ia_terrenos(banco_eleg, 19, 62, 73, 22, 140, 1)
    
    aux = database.copy()
    
    #Filtra os terrenos
    aux = filtra_coluna(aux, i_conta_contabil, 'Terrenos', '==')
    
    #Filtra o dataframe expurgando os ativos em que VNR é nulo
    ativos = filtra_coluna(aux, i_VNR, 0, '!=')
    
    #Calcula o VNR x IA
    #Multiplica VNR pelo IA:
    #Cria uma mascara no dataframe para os valores de IA diferentes de 0 (estes valores não devem ser multiplicados pois não se aplicam às categorias de ativos correspondentes)
    mask = (ativos.iloc[:,i_IA] != 0)
    #Cria um dataframe só com os valores validos para a multiplicação
    ativos_valid = ativos[mask]
    #Cria a coluna no dataframe com a conta a ser feita (sem multiplicar pelo IA)
    ativos = ativos*1
    ativos.loc[:,'VNR x IA'] = ativos.iloc[:, i_VNR]
    #Refaz a conta nas linhas em que o indice de aproveitamento não é nulo:
    ativos.loc[mask, 'VNR x IA'] = ativos_valid.iloc[:, i_VNR]*ativos_valid.iloc[:, i_IA]/100

    vnr_ia = ativos['VNR x IA'].sum()
    print("")
    print("VNR x IA: " + formats2(vnr_ia))
    print("")
    
    inf = lista_colunas(ativos)
    f_grupo = inf['Nome'][i_categoria]
    f_ordem = 'VNR x IA'
    f_qtde = inf['Nome'][i_qtde]
    aux = ativos*1
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='VNR x IA total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['VNR x IA médio/ativo'] = df_ordenado['VNR x IA total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('VNR x IA total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['VNR x IA total'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado['VNR x IA total [%]'] = df_ordenado['VNR x IA total']/df_ordenado['VNR x IA total'].sum()
    df_ordenado['VNR x IA acumulado'] = df_ordenado['VNR x IA total'].cumsum()/df_ordenado['VNR x IA total'].sum()
    
    print("")
    print("VNR x IA_Terrenos Total: " + str(custo_ativos))
    print("")
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['VNR x IA total'] = df_ordenado['VNR x IA total'].apply(formats2)
        df_ordenado['VNR x IA médio/ativo'] = df_ordenado['VNR x IA médio/ativo'].apply(formats2)
        df_ordenado['VNR x IA total [%]'] = df_ordenado['VNR x IA total [%]'].apply(formats3)
        df_ordenado['VNR x IA acumulado'] = df_ordenado['VNR x IA acumulado'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 31--------------------------------------------------


#__________________________________________________Script 32__________________________________________________
def dep_ia(database, i_categoria, i_dep, i_IA, i_qtde, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o dep_acum x IA
    #dep_ia(banco_eleg, 19, 70, 73, 22, 1)
    
    aux = database.copy()
    
    #Filtra o dataframe expurgando os ativos em que VNR é nulo
    ativos = filtra_coluna(aux, i_dep, 0, '!=')
    
    #Calcula o VNR x IA
    #Multiplica VNR pelo IA:
    #Cria uma mascara no dataframe para os valores de IA diferentes de 0 (estes valores não devem ser multiplicados pois não se aplicam às categorias de ativos correspondentes)
    mask = (ativos.iloc[:,i_IA] != 0)
    #Cria um dataframe só com os valores validos para a multiplicação
    ativos_valid = ativos[mask]
    #Cria a coluna no dataframe com a conta a ser feita (sem multiplicar pelo IA)
    ativos = ativos*1
    ativos.loc[:,'Dep_acum x IA'] = ativos.iloc[:, i_dep]
    #Refaz a conta nas linhas em que o indice de aproveitamento não é nulo:
    ativos.loc[mask, 'Dep_acum x IA'] = ativos_valid.iloc[:, i_dep]*ativos_valid.iloc[:, i_IA]/100

    dep_ia = ativos['Dep_acum x IA'].sum()
    print("")
    print("Dep_acum x IA: " + formats2(dep_ia))
    print("")
    
    inf = lista_colunas(ativos)
    f_grupo = inf['Nome'][i_categoria]
    f_ordem = 'Dep_acum x IA'
    f_qtde = inf['Nome'][i_qtde]
    aux = ativos*1
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='Dep_acum x IA total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado['Dep_acum x IA médio/ativo'] = df_ordenado['Dep_acum x IA total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('Dep_acum x IA total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['Dep_acum x IA total'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado['Dep_acum x IA total [%]'] = df_ordenado['Dep_acum x IA total']/df_ordenado['Dep_acum x IA total'].sum()
    df_ordenado['Dep_acum x IA acumulado'] = df_ordenado['Dep_acum x IA total'].cumsum()/df_ordenado['Dep_acum x IA total'].sum()
    
    print("")
    print("Dep_acum x IA Total: " + str(custo_ativos))
    print("")
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado['Dep_acum x IA total'] = df_ordenado['Dep_acum x IA total'].apply(formats2)
        df_ordenado['Dep_acum x IA médio/ativo'] = df_ordenado['Dep_acum x IA médio/ativo'].apply(formats2)
        df_ordenado['Dep_acum x IA total [%]'] = df_ordenado['Dep_acum x IA total [%]'].apply(formats3)
        df_ordenado['Dep_acum x IA acumulado'] = df_ordenado['Dep_acum x IA acumulado'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 32--------------------------------------------------


#__________________________________________________Script 33__________________________________________________
def transforma_data(xdata):
    # para transformar a data (de forma iterativa ou aplicando apply) do dataframe: 

    #Testa se é um valor numerico:
    if type(xdata) == int or type(xdata) == float:    
        #testa se o dado de entrada é int convertido em float:
        if xdata - int(xdata) == 0:
            #converte para int o dado de entrada
            aux = int(xdata)
            if aux == 0:
                #dt = 'Campo vazio'
                #dt = '01/01/3000'
                dt = datetime.strptime('01/01/2099', '%d/%m/%Y').isoformat()
            else:
                dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + aux - 2)
    else:
        #Verifica se é uma string no formato de data:
        if valida_data(xdata) == True:
            dt = datetime.strptime(xdata, '%d/%m/%Y').isoformat()
        else:
            #Copia o dado original
            dt = xdata

    return dt
#--------------------------------------------------Script 33--------------------------------------------------


#__________________________________________________Script 34__________________________________________________
def valida_data(data):
#Função para testar se a data está no formato adequado
    try:
        if data != datetime.strptime(data, "%d/%m/%Y").strftime('%d/%m/%Y'):
            raise ValueError
        return True
    except ValueError:
        return False
#--------------------------------------------------Script 34--------------------------------------------------


#__________________________________________________Script 35__________________________________________________
def calcula_no(database, i_categoria, i_VNR, i_CCV, i_dep, i_no, i_qtde, formatar):
    #agrupa o banco de dados por uma categoria específica e calcula o valor dos ativos não onerosos já depreciados
    #calcula_no(dados, 148, 62, 50, 45, 22, 1)

    #45 27 - ONEROSOS / NÃO ONEROSOS    
    aux = database.copy()
    
    #Filtra o dataframe selecionando os não onerosos
    ativos = filtra_coluna(aux, i_no, 'NÃO ONEROSOS', '==')
    
    #Desconta a depreciação acumulada em cada ativo
    ativos.loc[:,'NO - Dep_acum'] = ativos.iloc[:, i_VNR] + ativos.iloc[:, i_CCV] - ativos.iloc[:, i_dep]

    valor_no = ativos['NO - Dep_acum'].sum()
    print("")
    print("Não Onerosos - Dep_acum: " + formats2(valor_no))
    print("")
    
    inf = lista_colunas(ativos)
    f_grupo = inf['Nome'][i_categoria]
    f_ordem = 'NO - Dep_acum'
    f_qtde = inf['Nome'][i_qtde]
    aux = ativos*1
    
    #Filtra o dataframe expurgando os ativos em que (VNR x IA + CCV) é nulo
    aux = filtra_coluna(aux, len(aux.columns)-1, 0, '!=')
    
    #Dataframe agrupado e ordenado
    #df_qtde = aux.groupby([f_grupo]).size().reset_index(name='qtde ativos')
    df_qtde = aux.groupby([f_grupo])[f_qtde].sum().reset_index(name='Qtde ativos')
    df_custo = aux.groupby([f_grupo])[f_ordem].sum().reset_index(name='NO - Dep_acum total')
    df_ordenado = df_qtde.merge(df_custo)
    df_ordenado.loc[:,'NO - Dep_acum médio/ativo'] = df_ordenado['NO - Dep_acum total']/df_ordenado['Qtde ativos']
    df_qtde = []
    df_custo = []
    #df_ordenado = df_ordenado.sort_values('Custo total', ascending=aux_q_ordem).reset_index(drop=True)
    df_ordenado = df_ordenado.sort_values('NO - Dep_acum total', ascending=False).reset_index(drop=True)
    qtde_ativos = df_ordenado['Qtde ativos'].sum()
    custo_ativos = df_ordenado['NO - Dep_acum total'].sum()
    
    #Calcula representatividade relativa e acumulada
    df_ordenado.loc[:,'NO - Dep_acum total [%]'] = df_ordenado['NO - Dep_acum total']/df_ordenado['NO - Dep_acum total'].sum()
    df_ordenado.loc[:,'NO - Dep_acum acumulado'] = df_ordenado['NO - Dep_acum total'].cumsum()/df_ordenado['NO - Dep_acum total'].sum()
    
    print("")
    print("NO - Dep_acum Total: " + str(custo_ativos))
    print("")
    
    if formatar == 1:
        #Formata o DataFrame para exibição da moeda
        df_ordenado.loc[:,'NO - Dep_acum total'] = df_ordenado['NO - Dep_acum total'].apply(formats2)
        df_ordenado.loc[:,'NO - Dep_acum médio/ativo'] = df_ordenado['NO - Dep_acum médio/ativo'].apply(formats2)
        df_ordenado.loc[:,'NO - Dep_acum total [%]'] = df_ordenado['NO - Dep_acum total [%]'].apply(formats3)
        df_ordenado.loc[:,'NO - Dep_acum acumulado'] = df_ordenado['NO - Dep_acum acumulado'].apply(formats3)
    
    return df_ordenado
#--------------------------------------------------Script 35--------------------------------------------------


#__________________________________________________Script 36__________________________________________________
def importa_ipca(path):

    #Importa o arquivo excel do IBGE com as séries históricas
    #https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html?=&t=series-historicas
    
    #Importa arquivo excel (alterar a engine e comando de importação para ooutros formatos)
    dfs = pd.read_excel(path, sheet_name=0)
    #path = 'F:\HOMEOFFICE\SANEAMENTO\\ipca_202011SerieHist.xls'
    
    #Seleciona as 3 primeiras colunas, remove as linhas com valores NaN e também as duas ulltimas linhas de texto do dataframe
    dfs = dfs.iloc[:, 0:3].dropna(how='all')
    
    #Cria uma mascara marcando os valores numericos na primeira coluna
    mask = dfs.applymap(lambda x: isinstance(x, (int, float))).iloc[:,0]
    
    #filtra o dataframe utilizando a máscara
    dfs = dfs[mask]
    
    #Remove a primeira linha
    dfs = dfs.iloc[1:]
    
    #Ajusta os anos, remove valores que não sejam numeros
    for i in range(0, len(dfs)):
        aux = dfs.iloc[i, 0]
        #verifica se o valor é um número inteiro:
        if type(aux) == int:
            #anota o ano corrente:
            ano = str(aux)
            dfs.iloc[i,0] = ano
        #verifica se é Nan:
        if np.isnan(aux):
            #Altera o valor no dataframe
            dfs.iloc[i,0] = ano
    
    #Remove qualquer NaN restante
    dfs = dfs.dropna(how='any')
    
    #Ajusta os meses
    Tabela_mes = pd.DataFrame({'Mês_s': ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'], 'Mês_n': ['01','02','03','04','05','06','07','08','09', '10', '11', '12']})
    
    #Substitui os valores do dataframe conforme a tabela de correspondência
    for i in range(0, len(Tabela_mes)):
        dfs.iloc[:,1] = dfs.iloc[:,1].replace(Tabela_mes.iloc[i,0], Tabela_mes.iloc[i,1], regex=True)
    
    #Ajusta o cabeçalho
    dfs.columns = ['Ano', 'Mês', 'Índice']
    
    #Cria uma nova coluna com a data concatenada
    dfs['Data'] = "01/" + dfs.iloc[:,1] + "/" + dfs.iloc[:,0]
    
    #Transforma a data para formato ISO
    dfs['Data'] = dfs['Data'].apply(transforma_data)
    
    #Remove as duas primeiras colunas
    dfs = dfs.drop(['Ano', 'Mês'], axis = 1)

    #Reorganiza o dataframe
    dfs = dfs.reindex(columns=['Data', 'Índice'])
  
    #Converte para um formato de data mais simples:
    dfs['Data'] = pd.to_datetime(dfs['Data'])
    
    #Converte para numero do mês e ano:
    dfs['Data'] = dfs['Data'].apply(lambda x: x.strftime('%m/%Y'))
    
    dfs = dfs.reset_index()
   
    return dfs
#--------------------------------------------------Script 36--------------------------------------------------


#__________________________________________________Script 37__________________________________________________
def importa_igpm(path):
    
    #Importa o arquivo excel da FGVdados com a série histórica  do IGP-M
    #http://www14.fgv.br/fgvdados20/visualizaconsulta.aspx
    
    #Importa arquivo excel (alterar a engine e comando de importação para ooutros formatos)
    dfs = pd.read_excel(path, sheet_name=0, skiprows=np.arange(0, 14))
    #path = 'F:\HOMEOFFICE\SANEAMENTO\\IGP-M_11_2020.xls'
    
    #Seleciona as 2 primeiras colunas, remove as linhas com valores NaN e também as duas ulltimas linhas de texto do dataframe
    dfs = dfs.iloc[:, 0:2].dropna(how='all')
    
    #Ajusta o cabeçalho
    dfs.columns = ['Data', 'Índice']
    
    #Adiciona o dia 20 nos marcadores de data (IGP-M é medido do dia 21 do mês anterior ao dia 20 do mês de referencia):
    dfs['Data'] = '20/' + dfs['Data']
    
    #Transforma a data para formato ISO
    dfs['Data'] = dfs['Data'].apply(transforma_data)
    
    #Converte para um formato de data:
    dfs['Data'] = pd.to_datetime(dfs['Data'])
    
    #Converte para nome do mês e ano:
    #dfs['Data'].apply(lambda x: x.strftime('%B-%Y'))
    
    #Converte para numero do mês e ano:
    dfs['Data'] = dfs['Data'].apply(lambda x: x.strftime('%m/%Y'))
    
    dfs = dfs.reset_index()
    
    return dfs
#--------------------------------------------------Script 37--------------------------------------------------


#__________________________________________________Script 38__________________________________________________
def delta_indice(data_inicial, df_indice, data_final):

    df = df_indice
    lista_data = df_indice['Data'].to_list()
     
    #Verifica se a data inicial está contida no dataframe
    if data_inicial in lista_data:
        data_ini = True
    else:
        data_ini = False
        print("")
        print('Data inicial não encontrada!')
        print("")
    
    #Verifica se a data final está contida no dataframe
    if data_final in lista_data:
        data_end = True
    else:
        data_end = False
        print("")
        print('Data final não encontrada!')
        print("")
    
    #Calcula somente se encontrar as datas, senão retorna valor 0
    if data_ini == True and data_end == True:
        #Busca o índice da DataFrame em que a data base se encontra e retorna o valor do Índice
        indice_base = df['Índice'].loc[lista_data.index(data_inicial)-1]
        #Busca o índice da DataFrame em que a data de interesse se encontra e retorna o valor do Índice
        indice_final = df['Índice'].loc[lista_data.index(data_final)]
        #Calcula a variação
        delta = indice_final/indice_base
    else:
        delta = 0

    return delta
#--------------------------------------------------Script 38--------------------------------------------------

#__________________________________________________Script 39__________________________________________________
def importa_colunas(path):
    #Importa a lista de colunas descritas no sumario executivo da SETAPE (pag.478)
    
    #Importa arquivo excel (alterar a engine e comando de importação para ooutros formatos)
    dfs = pd.read_excel(path)
    #path = 'F:\HOMEOFFICE\SANEAMENTO\Planilhas_SETAPE\colunas_setape.xlsx'
    
    #Remove as linhas com valores NaN
    dfs = dfs.dropna()
    
    #Remove os espaços em branco
    dfs = remove_espacos(dfs)
    
    return dfs
#--------------------------------------------------Script 39--------------------------------------------------


#__________________________________________________Script 40__________________________________________________
def verifica_colunas(df_colunas, df_ref):
    #Compara a lista de colunas da planilha importada com a lista de referencia do sumario executivo
    
    lista_ref = df_ref['Nome'].to_list()
    lista_df = df_colunas['Nome'].to_list()
    
    #Avalia as diferenças em relação à referencia e guarda numa lista de índices
    lista_diff = []
    for i in range(0, len(lista_ref)):
        if lista_ref[i] != lista_df[i]:
            lista_diff.append(i)
        
    #Concatena os dois dataframes
    aux = pd.concat([df_ref, df_colunas], axis=1)
    
    #Guarda as diferenças
    aux_diff = aux.loc[lista_diff]
    
    return aux_diff
#--------------------------------------------------Script 40--------------------------------------------------

#__________________________________________________Script 41__________________________________________________
def compara_dataframe(banco1, banco2):
    #Compara os dois dataframes, coluna a coluna, e retorna a lista de índices das colunas discrepantes

    lista_diff = []
    for i in range(0, len(banco1.columns)):
        aux = banco1.iloc[:,i].to_list() == banco2.iloc[:,i].to_list()
        if aux == False:
            print('Colunas divergentes: ' + str(i))
            lista_diff.append(i)
    
    return lista_diff
#--------------------------------------------------Script 41--------------------------------------------------

#__________________________________________________Script 42__________________________________________________
def relatorio_divergencias(banco1, banco2, lista_divergencia):
    #Compara os dois dataframes, coluna a coluna, e retorna a lista de índices das colunas discrepantes
    
    for i in lista_divergencia:
        print('')
        print('___________________________________________________________________________________________')
        print('Coluna em análise: ' + str(i) + ' (' + banco1.columns[i] + ')')
        print('')
        print('DataFrame 1:')
        aux1 = opcoes_coluna(banco1, i)
        print(aux1)
        print('')
        print('DataFrame 2:')
        aux2 = opcoes_coluna(banco2, i)
        print(aux2)
        print('')
        if len(aux1) == len(aux2):
            df = aux1 == aux2
            print('Divergências: ')
            print(opcoes_coluna(banco1, i)[~(df.all(1))])
            print(opcoes_coluna(banco2, i)[~(df.all(1))])
        else:
            print('Número de linhas é diferente!')
    
    return
#--------------------------------------------------Script 42--------------------------------------------------

#__________________________________________________Script 43__________________________________________________
def filtra_data(database, indice_coluna, valor, condicao):
    #filtra o banco de dados por um indice de coluna e uma condição de data
    
    #condição: '>', '<', '!=' ou '=='
    #Exemplo:
    #dados_add = filtra_data(dados_tratados, 64, '2015-12-01', '>')
    #dados_add = filtra_data(dados_add, 64, '2099-01-01', '<')
    
    aux = database.copy()
    
    #Modifica o formato da data para realizar a operação de comparação
    aux = substitui_valor(aux, indice_coluna, 'Campo vazio', '01/2099')
    aux.iloc[:, indice_coluna] = pd.to_datetime(aux.iloc[:, indice_coluna])
    aux = filtra_coluna(aux, indice_coluna, valor, condicao)
    #dados_add = filtra_coluna(dados_add, 64, '2099-01-01', '<')
    aux.iloc[:, indice_coluna] = aux.iloc[:, indice_coluna].apply(lambda x: x.strftime('%m/%Y'))
    
    return aux
#--------------------------------------------------Script 43--------------------------------------------------


#__________________________________________________Script 44__________________________________________________
def importa_adicoes(path):
    #importa um arquivo das adições
    
    #'F:\HOMEOFFICE\SANEAMENTO\Adicoes 2016\Entradas 2016\ENTRADA_ELEGIVEIS_012016.TXT'
    
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\Anexo_3_BASE_INCREMENTAL_092020.txt'
    
    adicoes = pd.read_csv(path, sep=";", index_col=False, error_bad_lines=False, engine='python')
    
    soma_nan = adicoes.iloc[len(adicoes.index)-1,:].isnull().sum()
    
    #Verifica se a quantidade de NaN da ultima linha é maior que o limite:
    if soma_nan >= 20:
        #Remove a ultima linha
        adicoes = adicoes.iloc[0:len(adicoes.index)-2,:]

    return adicoes
#--------------------------------------------------Script 44--------------------------------------------------

#__________________________________________________Script 45__________________________________________________
def consolida_adicoes(pasta_raiz, extensao_arquivo, df_colunas_ref, altera_cabecalho):
    #Consolida os vários arquivos de banco de dados em um único e salva na raiz
    #Utilizar o dataframe com os cabeçalhos de referencia da SETAPE, importados utilizando o script importa_colunas
    #altera_cabecalho = 1: altera os cabeçalhos conforme o dataframe passado no argumento da função
    #altera_cabecalho = 0: não altera os cabeçalhos (modo report)
    #Exemplo de pasta raiz: pasta_raiz = 'F:\HOMEOFFICE\SANEAMENTO\Adicoes 2016\Entradas 2016'
    #Exemplo de formato: 'txt' (Por enquanto esta opção é manual, alterar linha 65 e dependencias)
    
    #Verifica qual é o sistema operacional
    sistema_op = os.name
    if sistema_op == 'nt':
        #Windows:
            formato = '\*.' + extensao_arquivo
    else:
        #Linux:
            formato = '/*.' + extensao_arquivo    
    
    #Lista as demais pastas do diretório
    lista_dir = [x[0] for x in os.walk(os.path.expanduser(pasta_raiz))]
    if len(lista_dir) > 1:
        lista_dir = sorted(lista_dir[1:len(lista_dir)])
    
    arquivos = []
    pastas = 0
    linhas = 0
    colunas = 0
    pontos = 0
    relatorio_arquivos = []
    all_data = pd.DataFrame([])
    #Roda para cada pasta:
    for k in lista_dir:
        pastas = pastas + 1
        aux_arquivos = 0
        #Print o nome de cada arquivo .xlsb encontrado em cada pasta do diretorio raiz
        for i in glob.glob(os.path.expanduser(k + formato)):
            arquivos.append(i)
            aux_arquivos = aux_arquivos + 1
            print(" ")
            print("___________________________________________________________________________________________________")
            print("Analisando o arquivo: " + os.path.basename(i))
            print("Pasta " + str(pastas) + " de " + str(len(lista_dir)) + " (" + os.path.basename(k) + ")")
            print("Arquivo " + str(aux_arquivos) + " de " + str(len(glob.glob(k + formato))))
        
            file_name = i
            
            print("Importando o arquivo...")
            
            #Importa arquivo (alterar a engine e comando de importação para outros formatos)
            if extensao_arquivo == 'pyxlsb':
                dfs = pd.read_excel(file_name, sheet_name=0, skiprows=[0], engine='pyxlsb')
            if extensao_arquivo == 'txt':
                dfs = pd.read_csv(file_name, sep=";", header=[0], engine='python')
            if extensao_arquivo == 'xlsx':
                dfs = pd.read_excel(file_name, sheet_name=0)
            
            #Verifica se o arquivo está vazio
            if len(dfs) <= 1:
                print('[ARQUIVO VAZIO] - ' + os.path.basename(i))
                relatorio_arquivos.append('[ARQUIVO VAZIO] - ' + i)
            else:
                #Verifica se a quantidade de NaN da ultima linha é maior que o limite:
                soma_nan = dfs.iloc[len(dfs.index)-1,:].isnull().sum()
                if soma_nan >= 20:
                    #Remove a ultima linha
                    dfs = dfs.iloc[0:len(dfs.index)-2,:]
    
                #Contabiliza o total de processamento
                linhas = linhas + len(dfs.index)
                colunas = colunas + len(dfs.columns)
                pontos = pontos + linhas*colunas
                
         
                #Tratamento inicial dos dados
                print(" ")
                print("Dados importados com sucesso!")
                print("Pré processando os dados...")
                
                print(str(len(arquivos)) + " Dataframes processados")
                print("Linhas processadas: " + str(len(dfs.index)))
                
                #Substitui os cabeçalhos do arquivo importado pelos cabeçalhos de referencia do sumario executivo da SETAPE
                if altera_cabecalho == 1:
                    for t in range(0, len(df_colunas_ref)):
                        dfs.rename(columns={dfs.columns[t]: df_colunas_ref['Nome'][t]}, inplace = True)
                
                #Verifica se as colunas estão compatíveis
                df_lista_colunas = lista_colunas(dfs)
                res_colunas = verifica_colunas(df_lista_colunas, df_colunas_ref)
                res_colunas.columns = ['REF', os.path.basename(i)]
                
                
                #Faz o tratamento dos dados
                #Substitui o separador decimal virgula por ponto nas colunas com numeros:
                for j in [24, 25, 27, 28, 29, 30]:
                    dfs.iloc[:,j] = dfs.iloc[:,j].map(formats4).astype(float)
                        
                #Cria a coluna de eligibilidade conforme o nome do arquivo:
                #Verifica se o nome do arquivo contém a palavra 'ENTRADA':
                nome_arquivo = os.path.basename(file_name)
                if 'ENTRADA' in nome_arquivo:
                    #Separa entre elegíveis, não elegíveis e não onerosos:
                    if 'NAO_ONEROSOS' in nome_arquivo:
                        dfs['27 - ONEROSOS / NÃO ONEROSOS'] = 'Adições 2016 - Entradas - NÃO ONEROSOS' 
                    if 'NAO_ELEGIVEIS' in nome_arquivo:
                         dfs['25 - ELEGIBILIDADE'] = 'Adições 2016 - Entradas - NÃO ELEGÍVEIS'
                    else:
                        if 'ELEGIVEIS' in nome_arquivo:
                            dfs['25 - ELEGIBILIDADE'] = 'Adições 2016 - Entradas - ELEGÍVEIS'
                else:
                    if 'IMOBILIZACOES' in nome_arquivo:
                        #Separa entre elegíveis, não elegíveis e não onerosos:
                        if 'NAO_ONEROSOS' in nome_arquivo:
                           dfs['27 - ONEROSOS / NÃO ONEROSOS'] = 'Adições 2016 - Imobilizações - NÃO ONEROSOS' 
                        if 'NAO_ELEGIVEIS' in nome_arquivo:
                            dfs['25 - ELEGIBILIDADE'] = 'Adições 2016 - Imobilizações - NÃO ELEGÍVEIS'
                        else:
                            if 'ELEGIVEIS' in nome_arquivo:
                                dfs['25 - ELEGIBILIDADE'] = 'Adições 2016 - Imobilizações - ELEGÍVEIS'
    
                #Substitui os espaços vazios (NaN) das demais colunas numericas pelo valor 0:
                for j in dfs.columns.to_list():
                    if is_numeric_dtype(dfs[j]):
                        dfs[j] = dfs[j].replace(np.nan, 0, regex=True)
                        
                #Substitui os zeros da coluna QUANTIDADE pelo valor unitario
                dfs.iloc[:,20] = dfs.iloc[:,20].replace(0, 1, regex=True)
               
                #Substitui os espaços vazios (NaN) do dataframe pela string 'Campo vazio'
                dfs = dfs.replace(np.nan, 'Campo vazio', regex=True)
                dfs = dfs.replace('00/00/0000', 'Campo vazio', regex=True)
    
                #Remove o excesso de espaços nos cabeçalhos
                dfs.columns = dfs.columns.str.replace(r'\s\s', ' ')
                
                #Converte os formatos de data para time stamps do pandas
                #Colunas 22, 23, 26
                aux_col = [22, 23, 26]
                for m in aux_col:
                    #Remove a string:
                    dfs.iloc[:, m] = dfs.iloc[:, m].replace('Campo vazio', 0, regex=True)
                    #Converte para timestamp
                    dfs.iloc[:, m] = dfs.iloc[:, m].apply(transforma_data)
    
                    #Converte para um formato de data mais simples:
                    dfs.iloc[:, m] = pd.to_datetime(dfs.iloc[:, m])
                    #Converte para numero do mês e ano:
                    dfs.iloc[:, m] = dfs.iloc[:, m].apply(lambda x: x.strftime('%m/%Y'))
                    #Substitui os marcadores de data do dataframe pela string 'Campo vazio'
                    dfs.iloc[:, m] = dfs.iloc[:, m].replace('01/2099', 'Campo vazio', regex=True)
    
                #Concatena os multiplos dataframes em um único dataframe
                all_data = all_data.append(dfs, ignore_index=True)
                
                print("Linhas armazenadas: " + str(len(all_data.index)))
                print("")
    
                print('___________________________________________________')
                print(res_colunas)
                print('___________________________________________________')
                print("")            
                
                #Anota as opções de cada coluna para verificação ao final
                relatorio_arquivos.append(i)
     
    print(" ")
    #Resumo do processamento   
    print("____________________________________RESUMO____________________________________")
    print("Arquivos analisados: " + str(len(arquivos)))
    print("Linhas processadas: " + str(linhas))
    print("Colunas processadas: " + str(colunas))
    print("Pontos processados: " + str(pontos))
    print(" ")
    
    print("Lista de arquivos processados: ")
    for i in relatorio_arquivos:
        print(i)
    
    #Salva o DataFrame tratado como hdf5
    print(" ")
    print("Tamanho do DataFrame final: " + str(len(all_data)))
    print(" ")
    print("Salvando o banco de dados consolidado...")
    save_file_name = pasta_raiz + '\DB_adicoes_2016_consolidado.h5'
    all_data.to_hdf(save_file_name, key='all_data', mode='w')
    print("Arquivo salvo no seguinte local: ")
    print(save_file_name)
    
    return all_data
#--------------------------------------------------Script 45--------------------------------------------------

#formats2(adicoes_2016.iloc[:, 28].apply(formats4).astype(float).sum())
#adicoes_2016.iloc[:, 30].apply(formats4).astype(float).sum()


#__________________________________________________Script 46__________________________________________________
def busca_item(database, item):
    #Aponta as colunas que contém o item buscado
    
    colunas = []
    for i in range(0, len(database.columns)):
        lista = str(database.iloc[:, i].map(str).to_list())
        if item in lista:
            print(i)
            colunas.append(i)

    return colunas
#--------------------------------------------------Script 46--------------------------------------------------


#__________________________________________________Script 47__________________________________________________
def insere_database_inicial(database, data_laudo_1RTP):
    #Inclui coluna de database inicial de atualização dos ativos
    
    aux = database.copy()
    
    aux.loc[:, 'Data base inicial - 2ª RTP'] = data_laudo_1RTP

    return aux
#--------------------------------------------------Script 47--------------------------------------------------


#__________________________________________________Script 48__________________________________________________
def insere_database_final(database, data_laudo_2RTP):
    #Inclui coluna de database final de atualização dos ativos
    
    aux = database.copy()
    
    aux.loc[:, 'Data base final - 2ª RTP'] = data_laudo_2RTP

    return aux
#--------------------------------------------------Script 48--------------------------------------------------

#__________________________________________________Script 49__________________________________________________
def insere_variacao_tempo(database, i_data_ini, i_data_final):
    #Inclui coluna de lapso temporal [meses] entre data base inicial e final de atualização dos ativos
    
    aux = database.copy()
    
    #Atualiza temporariamente o formato de data das colunas de interesse
    data_ini = pd.to_datetime(aux.iloc[:, i_data_ini])
    data_final = pd.to_datetime(aux.iloc[:, i_data_final])
    
    aux.loc[:, 'Variação [meses] - 2ª RTP'] = data_final.map(delta_mes) - data_ini.map(delta_mes)
    
    return aux
#--------------------------------------------------Script 49--------------------------------------------------


#__________________________________________________Script 50__________________________________________________
def insere_variacao_indice(database, tipo_indice, df_indice):
    #Inclui coluna de database de atualização dos ativos
    
    aux = database.copy()
    
    if tipo_indice == 'igpm' or tipo_indice == 'IGPM':
        indice = 'IGP-M'
    else:
        if tipo_indice == 'ipca' or tipo_indice == 'IPCA':
            indice = 'IPCA'
        else:
            print('Erro! ìndice econômico não reconhecido!')
        
    #Verifica se há uma data base inicial única
    datas_ini = len(opcoes_coluna(database, database.columns.get_loc("Data base inicial - 2ª RTP")))
    if datas_ini == 1:
        data_inicial = opcoes_coluna(database, database.columns.get_loc("Data base inicial - 2ª RTP")).iloc[0,0]
    else:
       print('Erro na data base inicial!')
       data_inicial = 0
    
    #Verifica se há uma data base final única
    datas_fim = len(opcoes_coluna(database, database.columns.get_loc("Data base final - 2ª RTP")))
    if datas_fim == 1:
        data_final = opcoes_coluna(database, database.columns.get_loc("Data base final - 2ª RTP")).iloc[0,0]
    else:
       print('Erro na data base final!')
       data_final = 0 
    
    #Calcula a variação do índice
    variacao = delta_indice(data_inicial, df_indice, data_final)
    
    #Insere a variação do índice no dataframe
    aux.loc[:, 'Variação do ' + indice + ' - 2ª RTP'] = variacao

    return aux
#--------------------------------------------------Script 50--------------------------------------------------


#__________________________________________________Script 51__________________________________________________
def insere_taxa_dep(database, i_dep, i_op, i_data_base):
    #Calcula a taxa de depreciação regulatória de cada ativo
    #i_data_base: database da 1ª RTP
    #i_op: data de entrada em operação do ativo
    #i_dep: depreciação regulatória acumulada [%]
    #insere_taxa_dep(dados_atualizados, 71, 49, 141)
    
    aux = database.copy()
    
    #Trata os campos vazios como uma data fictícia
    mask = (aux.iloc[:, i_op] == 'Campo vazio')
    aux.loc[mask, aux.columns[i_op]] = '01/2099'
    
    data_ini = pd.to_datetime(aux.iloc[:, i_op])
    data_final = pd.to_datetime(aux.iloc[:, i_data_base])
    
    aux.loc[:, 'Vida útil consumida - 1ª RTP'] = data_final.map(delta_mes) - data_ini.map(delta_mes)
    aux.loc[:, 'Taxa Dep regulatória [% a.m.] - 1ª RTP'] = aux.iloc[:, i_dep]/aux.loc[:, 'Vida útil consumida - 1ª RTP']
    
    #Substitui os valores infinitos por 0
    mask_inf = (aux.loc[:, 'Taxa Dep regulatória [% a.m.] - 1ª RTP'] == np.inf)
    aux.loc[mask_inf, 'Taxa Dep regulatória [% a.m.] - 1ª RTP'] = 0
    
    #Retorna os Campo vazio
    aux.loc[mask, aux.columns[i_op]] = 'Campo vazio - 1ª RTP'
    
    #Insere Campo vazio nos ativos com vida útil negativa
    mask =  (aux.loc[:, 'Vida útil consumida - 1ª RTP'] < 0)
    aux.loc[mask, 'Vida útil consumida - 1ª RTP'] = 'Campo vazio - 1ª RTP'
    aux.loc[mask, 'Taxa Dep regulatória [% a.m.] - 1ª RTP'] = 'Campo vazio - 1ª RTP'
    
    #Trata os ativos cuja depreciação acumulada é nula porém possuem taxa de depreciação contábil
    #Exclui terrenos e RO:
    mask1 = ((aux.iloc[:, 140] != 'Terrenos') & (aux.iloc[:, 43] != 'ELEGÍVEIS-RO') & (aux.iloc[:, 70] == 0))
    #Copia o valor da taxa de depreciação contábil
    aux.loc[mask1, 'Taxa Dep regulatória [% a.m.] - 1ª RTP'] = aux.loc[mask1, aux.columns[27]]
    
    return aux
#--------------------------------------------------Script 51--------------------------------------------------
  


#__________________________________________________Script 52__________________________________________________
def atualiza_dep_ia(database, i_taxa_deprec, i_IA):
    #Atualiza o valor depreciado acumulado dos ativos pela taxa de depreciação de cada ativo e o Indice de aproveitamento
    
    aux = database.copy()
    
    #Trata os campos vazios
    mask = (aux.loc[:, 'Vida útil consumida - 1ª RTP'] == 'Campo vazio - 1ª RTP')
    aux.loc[mask, 'Vida útil consumida - 1ª RTP'] = 0
    
    #Calcula a vida útil consumida total: vida util consumida até a database da 1ª RTP + lapso temporal até a database final da 2ª RTP
    aux.loc[:, 'Vida útil consumida - 2ª RTP'] =  aux.loc[:, 'Vida útil consumida - 1ª RTP'] + aux.loc[:, 'Variação [meses] - 2ª RTP']
    
    #Retorna a tag de Campo vazio
    aux.loc[mask, 'Vida útil consumida - 1ª RTP'] = 'Campo vazio - 1ª RTP'
    
    #Atualiza a depreciação acumulada %
    aux.loc[:, 'DEP. ACUM. REG. - 2ª RTP (%)'] = aux.loc[:, 'Vida útil consumida - 2ª RTP']*aux.iloc[:,i_taxa_deprec]
    
    #Para as sobras físicas, copia a depreciação acumulada da 1ª RTP (congelamento da depreciação)
    aux.loc[mask, 'DEP. ACUM. REG. - 2ª RTP (%)'] = aux.iloc[:, 71]
    
    #Substitui os valores que forem maiores que 100% por 100%
    mask = (aux.loc[:, 'DEP. ACUM. REG. - 2ª RTP (%)'] > 100)
    aux.loc[mask, 'DEP. ACUM. REG. - 2ª RTP (%)'] = 100
    
    #Calcula a depreciação acumulada multiplicando o percentual pelo VNR + CCV
    aux.loc[:, 'DEP. ACUM. REG. - 2ª RTP (R$)'] = (aux.loc[:, 'DEP. ACUM. REG. - 2ª RTP (%)']/100)*(aux.iloc[:,62] + aux.iloc[:,81])
    
    #Atualiza IA
    #Cria uma mascara para substituir os valores nulos por valor unitário
    mask = (aux.iloc[:, i_IA] == 0)
    aux.loc[:, 'ÍNDICE DE APROVEITAMENTO (IA) [%] - 2ª RTP'] = aux.iloc[:, i_IA]
    aux.loc[mask, 'ÍNDICE DE APROVEITAMENTO (IA) [%] - 2ª RTP'] = 100
    
    return aux
#--------------------------------------------------Script 52--------------------------------------------------


#__________________________________________________Script 53__________________________________________________
def delta_mes(data):
    return 12 * data.year + data.month
#--------------------------------------------------Script 53--------------------------------------------------


#__________________________________________________Script 54__________________________________________________
def atualiza_VNR_CCV(database, i_VNR, i_CCV, i_indice, nome_indice):
    #Atualiza o valor do VNR pelo índice economico indicado
    
    aux = database.copy()
    
    #Atualiza VNR
    key = 'VNR atualizado [' + nome_indice + '] - 2ª RTP (R$)'
    aux.loc[:, key] = aux.iloc[:, i_VNR]*aux.iloc[:,i_indice]
    
    key = 'CCV atualizado [' + nome_indice + '] - 2ª RTP (R$)'
    aux.loc[:, key] = aux.iloc[:, i_CCV]*aux.iloc[:,i_indice]
     
    return aux
#--------------------------------------------------Script 54--------------------------------------------------

#__________________________________________________Script 55__________________________________________________
def atualiza_Dep_VMU(database, i_indice, nome_indice):
    #Atualiza a depreciação acumulada, o VMU e o VMU descontado IA pelo índice economico indicado
    
    aux = database.copy()
    
    #Atualiza Depreciação acumulada
    key = 'DEP. ACUM. REG. [' + nome_indice + '] - 2ª RTP (R$)'
    aux.loc[:, key] = aux.loc[:, 'DEP. ACUM. REG. - 2ª RTP (R$)']*aux.iloc[:,i_indice]
   
    #Atualiza VMU: (CCV + VNR) - Dep
    key = 'VMU [' + nome_indice + '] - 2ª RTP (R$)'
    aux.loc[:, key] = (aux.loc[:, 'VNR atualizado [' + nome_indice + '] - 2ª RTP (R$)']) + (aux.loc[:, 'CCV atualizado [' + nome_indice + '] - 2ª RTP (R$)']) - (aux.loc[:, 'DEP. ACUM. REG. [' + nome_indice + '] - 2ª RTP (R$)'])
    
    #Atualiza VMU x IA
    key = 'VMU x IA [' + nome_indice + '] - 2ª RTP (R$)'
    aux.loc[:, key] = aux.loc[:, 'VMU [' + nome_indice + '] - 2ª RTP (R$)']*aux.loc[:, 'ÍNDICE DE APROVEITAMENTO (IA) [%] - 2ª RTP']/100
     
    return aux
#--------------------------------------------------Script 55--------------------------------------------------


#__________________________________________________Script 56__________________________________________________
def atualiza_banco(dados):
    #Sequencia de passos para atualização da base de dados
    #Requisitos: carregar dados IGP-M e IPCA, banco de dados com 140 colunas
    
    print(' ')
    print('Iniciando processo de atualização')
    print(' ')
    
    print('Passo 1/12: importando séries históricas dos índices econômicos...')
    path = 'F:\HOMEOFFICE\SANEAMENTO\\IGP-M_11_2020.xls'
    igpm = importa_igpm(path)
    
    path = 'F:\HOMEOFFICE\SANEAMENTO\\ipca_202011SerieHist.xls'
    ipca = importa_ipca(path)
    
    print('Passo 2/12: inserindo a database inicial: 12/2015...')
    dados_atualizados = insere_database_inicial(dados, '12/2015')
    print('Passo 3/12: inserindo a database inicial: 11/2020...')
    dados_atualizados = insere_database_final(dados_atualizados, '11/2020')
    print('Passo 4/12: inserindo a variação temporal...')
    dados_atualizados = insere_variacao_tempo(dados_atualizados, 141, 142)
    print('Passo 5/12: inserindo a variação do índice IGP-M...')
    dados_atualizados = insere_variacao_indice(dados_atualizados, 'igpm', igpm)
    print('Passo 6/12: inserindo a variação do índice IPCA...')
    dados_atualizados = insere_variacao_indice(dados_atualizados, 'ipca', ipca)
    print('Passo 7/12: inserindo a taxa de depreciação regulatória...')
    dados_atualizados = insere_taxa_dep(dados_atualizados, 71, 49, 141)
    print('Passo 8/12: atualizando a depreciação regulatória acumulada...')
    dados_atualizados = atualiza_dep_ia(dados_atualizados, 147, 73)
    print('Passo 9/12: atualizando a VNR e CCV pelo IGP-M...')
    dados_atualizados = atualiza_VNR_CCV(dados_atualizados, 62, 81, 144, 'IGP-M')
    print('Passo 10/12: atualizando a depreciação acumulada e o VMU pelo IGP-M...')
    dados_atualizados = atualiza_Dep_VMU(dados_atualizados, 144, 'IGP-M')
    print('Passo 11/12: atualizando a VNR e CCV pelo IPCA...')
    dados_atualizados = atualiza_VNR_CCV(dados_atualizados, 62, 81, 145, 'IPCA')
    print('Passo 12/12: atualizando depreciação acumulada e o VMU pelo IPCA...')
    dados_atualizados = atualiza_Dep_VMU(dados_atualizados, 145, 'IPCA')
    
    print('Atualização completada com sucesso!')
    print('Por gentileza executar o comando verifica_atualizacao')
    
    return dados_atualizados
#--------------------------------------------------Script 56--------------------------------------------------


#__________________________________________________Script 57__________________________________________________
def verifica_atualizacao(dados, dados_atualizados):
    #Verifica atualização da depreciação do dataframe original e do atualizado
    
    print(lista_colunas(dados_atualizados))

    print(' ')
    a = filtra_coluna(dados_atualizados, 147, 'Campo vazio - 1ª RTP', '!=')
    print('Taxa de depreciação média 1ª RTP [% a.m.]: ' + formats3(a.iloc[:, 147].mean()/100))
    print('Depreciação média 1ª RTP: ' + formats3(dados_atualizados.iloc[:, 71].mean()/100))
    print('Depreciação média 2ª RTP: ' + formats3(dados_atualizados.loc[:, 'DEP. ACUM. REG. - 2ª RTP (%)'].mean()/100))
    
    #Verifica os 100% Depreciados
    ativos, baixados = baixa_ativos(dados, 71)
    print(' ')
    print('Depreciação ativos baixados 1ª RTP: ' + formats2(dep_ia(baixados, 19, 70, 73, 55, 0).iloc[:, 2].sum()))
    ativos, baixados = baixa_ativos(dados_atualizados, 149)
    print('Depreciação ativos baixados 2ª RTP: ' + formats2(dep_ia(baixados, 19, 150, 73, 55, 0).iloc[:, 2].sum()))
    
    #Verifica atualização pelo IGP-M
    print(' ')
    print('VNR 1ª RTP: ' + formats2(dados_atualizados.iloc[:, 62].sum()))
    print('VNR 2ª RTP [IGP-M]: ' + formats2(dados_atualizados.loc[:, 'VNR atualizado [IGP-M] - 2ª RTP (R$)'].sum()))
    print('CCV 1ª RTP: ' + formats2(dados_atualizados.iloc[:, 81].sum()))
    print('CCV 2ª RTP [IGP-M]: ' + formats2(dados_atualizados.loc[:, 'CCV atualizado [IGP-M] - 2ª RTP (R$)'].sum()))
    print('Variação VNR [IGP-M]: ' + formats3(dados_atualizados.loc[:, 'VNR atualizado [IGP-M] - 2ª RTP (R$)'].sum()/dados_atualizados.iloc[:, 62].sum() - 1))
    print('Variação CCV [IGP-M]: ' + formats3(dados_atualizados.loc[:, 'CCV atualizado [IGP-M] - 2ª RTP (R$)'].sum()/dados_atualizados.iloc[:, 81].sum() - 1))
    print('Variação IGP-M: ' + formats3(dados_atualizados.loc[:, 'Variação do IGP-M - 2ª RTP'].mean() - 1))
    
    #verifica atualização pelo IPCA
    print(' ')
    print('VNR 1ª RTP: ' + formats2(dados_atualizados.iloc[:, 62].sum()))
    print('VNR 2ª RTP [IPCA]: ' + formats2(dados_atualizados.loc[:, 'VNR atualizado [IPCA] - 2ª RTP (R$)'].sum()))
    print('CCV 1ª RTP: ' + formats2(dados_atualizados.iloc[:, 81].sum()))
    print('CCV 2ª RTP [IPCA]: ' + formats2(dados_atualizados.loc[:, 'CCV atualizado [IPCA] - 2ª RTP (R$)'].sum()))
    print('Variação VNR [IPCA]: ' + formats3(dados_atualizados.loc[:, 'VNR atualizado [IPCA] - 2ª RTP (R$)'].sum()/dados_atualizados.iloc[:, 62].sum() - 1))
    print('Variação CCV [IPCA]: ' + formats3(dados_atualizados.loc[:, 'CCV atualizado [IPCA] - 2ª RTP (R$)'].sum()/dados_atualizados.iloc[:, 81].sum() - 1))
    print('Variação IPCA: ' + formats3(dados_atualizados.loc[:, 'Variação do IPCA - 2ª RTP'].mean() - 1))
#--------------------------------------------------Script 57--------------------------------------------------


#__________________________________________________Script 58__________________________________________________
def calcula_taxa_dep_media(dados_atualizados, i_dep, i_taxa_dep):
    #Utilizar i_dep = 71 para o cálculo referente à 1ª RTP
    #Utilizar i_dep = 149 para o cálculo referente à 2ª RTP
    nao_elegiveis = filtra_coluna(dados_atualizados, 43, 'NÃO ELEGÍVEIS', '!=')
    nao_elegiveis = filtra_coluna(nao_elegiveis, 43, 'Campo vazio', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis, 46, 'SOBRA FÍSICA', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 45, 'NÃO ONEROSOS', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 140, 'Terrenos', '!=')
    nao_elegiveis_conta_dep, baixados = baixa_ativos(nao_elegiveis_conta_dep, i_dep)
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 147, 'Campo vazio - 1ª RTP', '!=')

    nao_elegiveis_conta_dep.loc[:, 'Aux Dep contabil media'] = nao_elegiveis_conta_dep.iloc[:, i_taxa_dep]*(nao_elegiveis_conta_dep.iloc[:, 62] + nao_elegiveis_conta_dep.iloc[:, 81])
    print('')
    print('Taxa de depreciação média contábil ponderada por VNR+CCV: ' + formats3(nao_elegiveis_conta_dep.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep.iloc[:, 62] + nao_elegiveis_conta_dep.iloc[:, 81]).sum()*12/100))
    
    nao_elegiveis_conta_dep.loc[:, 'Aux Dep regulatoria media'] = nao_elegiveis_conta_dep.iloc[:, 147]*(nao_elegiveis_conta_dep.iloc[:, 62] + nao_elegiveis_conta_dep.iloc[:, 81])
    print('Taxa de depreciação média regulatória ponderada por VNR+CCV: ' + formats3(nao_elegiveis_conta_dep.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep.iloc[:, 62] + nao_elegiveis_conta_dep.iloc[:, 81]).sum()*12/100))
    
    #Separa em serviço de água e esgoto
    nao_elegiveis_conta_dep_agua = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ÁGUA', '==')
    nao_elegiveis_conta_dep_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ESGOTO', '==')
    
    #% AGUA
    print('')
    print('Taxa de depreciação média contábil ponderada por VNR+CCV [ÁGUA]: ' + formats3(nao_elegiveis_conta_dep_agua.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep_agua.iloc[:, 62] + nao_elegiveis_conta_dep_agua.iloc[:, 81]).sum()*12/100))
    print('Taxa de depreciação média regulatória ponderada por VNR+CCV [ÁGUA]: ' + formats3(nao_elegiveis_conta_dep_agua.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_agua.iloc[:, 62] + nao_elegiveis_conta_dep_agua.iloc[:, 81]).sum()*12/100))
    
    #% ESGOTO
    print('')
    print('Taxa de depreciação média contábil ponderada por VNR+CCV [ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_esgoto.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep_esgoto.iloc[:, 62] + nao_elegiveis_conta_dep_esgoto.iloc[:, 81]).sum()*12/100))
    print('Taxa de depreciação média regulatória ponderada por VNR+CCV [ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_esgoto.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_esgoto.iloc[:, 62] + nao_elegiveis_conta_dep_esgoto.iloc[:, 81]).sum()*12/100))
    
    #%AGUA + ESGOTO
    print('')
    nao_elegiveis_conta_dep_agua_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ADMINISTRAÇÃO', '!=')
    print('Taxa de depreciação média contábil ponderada por VNR+CCV [ÁGUA + ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_agua_esgoto.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 62] + nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 81]).sum()*12/100))
    print('Taxa de depreciação média regulatória ponderada por VNR+CCV [ÁGUA + ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_agua_esgoto.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 62] + nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 81]).sum()*12/100))
    
#--------------------------------------------------Script 58--------------------------------------------------


#__________________________________________________Script 59__________________________________________________
def calcula_dep_media_qtde(dados_atualizados, i_dep):
    #Utilizar i_dep = 71 para o cálculo referente à 1ª RTP
    #Utilizar i_dep = 149 para o cálculo referente à 2ª RTP
    nao_elegiveis = filtra_coluna(dados_atualizados, 43, 'NÃO ELEGÍVEIS', '!=')
    nao_elegiveis = filtra_coluna(nao_elegiveis, 43, 'Campo vazio', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis, 46, 'SOBRA FÍSICA', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 45, 'NÃO ONEROSOS', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 140, 'Terrenos', '!=')
    nao_elegiveis_conta_dep, baixados = baixa_ativos(nao_elegiveis_conta_dep, i_dep)
    
    nao_elegiveis_conta_dep.loc[:, 'Aux Dep contabil media'] = nao_elegiveis_conta_dep.iloc[:, 27]*(nao_elegiveis_conta_dep.iloc[:, 55])
    print('')
    print('Taxa de depreciação média contábil ponderada por QTDE: ' + formats3(nao_elegiveis_conta_dep.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep.iloc[:, 55]).sum()/100))
    
    nao_elegiveis_conta_dep.loc[:, 'Aux Dep regulatoria media'] = nao_elegiveis_conta_dep.iloc[:, 147]*(nao_elegiveis_conta_dep.iloc[:, 55])
    print('Taxa de depreciação média regulatória ponderada por QTDE: ' + formats3(nao_elegiveis_conta_dep.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep.iloc[:, 55]).sum()*12/100))
    
    #Separa em serviço de água e esgoto
    nao_elegiveis_conta_dep_agua = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ÁGUA', '==')
    nao_elegiveis_conta_dep_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ESGOTO', '==')
    
    #% AGUA
    print('')
    print('Taxa de depreciação média contábil ponderada por QTDE [ÁGUA]: ' + formats3(nao_elegiveis_conta_dep_agua.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep_agua.iloc[:, 55]).sum()/100))
    print('Taxa de depreciação média regulatória ponderada por QTDE [ÁGUA]: ' + formats3(nao_elegiveis_conta_dep_agua.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_agua.iloc[:, 55]).sum()*12/100))
    
    #% ESGOTO
    print('')
    print('Taxa de depreciação média contábil ponderada por QTDE [ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_esgoto.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep_esgoto.iloc[:, 55]).sum()/100))
    print('Taxa de depreciação média regulatória ponderada por QTDE [ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_esgoto.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_esgoto.iloc[:, 55]).sum()*12/100))
    
    #%AGUA + ESGOTO
    print('')
    nao_elegiveis_conta_dep_agua_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ADMINISTRAÇÃO', '!=')
    print('Taxa de depreciação média contábil ponderada por QTDE [ÁGUA + ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_agua_esgoto.loc[:, 'Aux Dep contabil media'].sum()/(nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 55]).sum()/100))
    print('Taxa de depreciação média regulatória ponderada por QTDE [ÁGUA + ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_agua_esgoto.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 55]).sum()*12/100))
    
#--------------------------------------------------Script 59--------------------------------------------------


#__________________________________________________Script 60__________________________________________________
def calcula_dep_media_simples(dados_atualizados, i_dep):
    #Utilizar i_dep = 71 para o cálculo referente à 1ª RTP
    #Utilizar i_dep = 149 para o cálculo referente à 2ª RTP
    nao_elegiveis = filtra_coluna(dados_atualizados, 43, 'NÃO ELEGÍVEIS', '!=')
    nao_elegiveis = filtra_coluna(nao_elegiveis, 43, 'Campo vazio', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis, 46, 'SOBRA FÍSICA', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 45, 'NÃO ONEROSOS', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 140, 'Terrenos', '!=')
    nao_elegiveis_conta_dep, baixados = baixa_ativos(nao_elegiveis_conta_dep, i_dep)
    
    media_contabil = nao_elegiveis_conta_dep.iloc[:, 27].mean()
    print('')
    print('Taxa de depreciação média contábil: ' + formats3(media_contabil/100))
    
    media_regulatoria = nao_elegiveis_conta_dep.iloc[:, 147].mean()
    print('Taxa de depreciação média regulatória: ' + formats3(media_regulatoria*12/100))
    
    #Separa em serviço de água e esgoto
    nao_elegiveis_conta_dep_agua = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ÁGUA', '==')
    nao_elegiveis_conta_dep_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ESGOTO', '==')
    
    #% AGUA
    print('')
    media_contabil_agua = nao_elegiveis_conta_dep_agua.iloc[:, 27].mean()
    print('Taxa de depreciação média [ÁGUA]: ' + formats3(media_contabil_agua/100))
    media_regulatoria_agua = nao_elegiveis_conta_dep_agua.iloc[:, 147].mean()
    print('Taxa de depreciação média regulatória [ÁGUA]: ' + formats3(media_regulatoria_agua*12/100))
    
    #% ESGOTO
    print('')
    media_contabil_esgoto = nao_elegiveis_conta_dep_esgoto.iloc[:, 27].mean()
    print('Taxa de depreciação média contábil [ESGOTO]: ' + formats3(media_contabil_esgoto/100))
    media_regulatoria_esgoto = nao_elegiveis_conta_dep_esgoto.iloc[:, 147].mean()
    print('Taxa de depreciação média regulatória [ESGOTO]: ' + formats3(media_regulatoria_esgoto*12/100))
    
    #%AGUA + ESGOTO
    nao_elegiveis_conta_dep_agua_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ADMINISTRAÇÃO', '!=')
    print('')
    media_contabil_agua_esgoto = nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 27].mean()
    print('Taxa de depreciação média contábil [ÁGUA + ESGOTO]: ' + formats3(media_contabil_agua_esgoto/100))
    media_regulatoria_agua_esgoto = nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 147].mean()
    print('Taxa de depreciação média regulatória [ÁGUA + ESGOTO]: ' + formats3(media_regulatoria_agua_esgoto*12/100))
    
#--------------------------------------------------Script 60--------------------------------------------------


#__________________________________________________Script 61__________________________________________________
def calcula_dep_acum_media(dados_atualizados, i_dep):
    #Utilizar i_dep = 71 para o cálculo referente à 1ª RTP
    #Utilizar i_dep = 149 para o cálculo referente à 2ª RTP
    nao_elegiveis = filtra_coluna(dados_atualizados, 43, 'NÃO ELEGÍVEIS', '!=')
    nao_elegiveis = filtra_coluna(nao_elegiveis, 43, 'Campo vazio', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis, 46, 'SOBRA FÍSICA', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 45, 'NÃO ONEROSOS', '!=')
    nao_elegiveis_conta_dep = filtra_coluna(nao_elegiveis_conta_dep, 140, 'Terrenos', '!=')
    nao_elegiveis_conta_dep, baixados = baixa_ativos(nao_elegiveis_conta_dep, i_dep)

    nao_elegiveis_conta_dep.loc[:, 'Aux Dep regulatoria media'] = nao_elegiveis_conta_dep.iloc[:, i_dep]*(nao_elegiveis_conta_dep.iloc[:, 62] + nao_elegiveis_conta_dep.iloc[:, 81])
    print('Depreciação média regulatória ponderada por VNR+CCV: ' + formats3(nao_elegiveis_conta_dep.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep.iloc[:, 62] + nao_elegiveis_conta_dep.iloc[:, 81]).sum()/12/100))
    
    #Separa em serviço de água e esgoto
    nao_elegiveis_conta_dep_agua = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ÁGUA', '==')
    nao_elegiveis_conta_dep_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ESGOTO', '==')
    
    #% AGUA
    print('')
    print('Depreciação média regulatória ponderada por VNR+CCV [ÁGUA]: ' + formats3(nao_elegiveis_conta_dep_agua.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_agua.iloc[:, 62] + nao_elegiveis_conta_dep_agua.iloc[:, 81]).sum()/12/100))
    
    #% ESGOTO
    print('')
    print('Depreciação média regulatória ponderada por VNR+CCV [ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_esgoto.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_esgoto.iloc[:, 62] + nao_elegiveis_conta_dep_esgoto.iloc[:, 81]).sum()/12/100))
    
    #%AGUA + ESGOTO
    print('')
    nao_elegiveis_conta_dep_agua_esgoto = filtra_coluna(nao_elegiveis_conta_dep, 19, 'ADMINISTRAÇÃO', '!=')
    print('Depreciação média regulatória ponderada por VNR+CCV [ÁGUA + ESGOTO]: ' + formats3(nao_elegiveis_conta_dep_agua_esgoto.loc[:, 'Aux Dep regulatoria media'].sum()/(nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 62] + nao_elegiveis_conta_dep_agua_esgoto.iloc[:, 81]).sum()/12/100))
    
#--------------------------------------------------Script 61--------------------------------------------------



#ARSAE-MG:
#equipe economica BAR: 5 servidores: 1 gerente, 2  economistas e 2 engenheiros
#verificação (fiscalização): 8 a 10 para fiscalização operacional
    #5 pessoas para fiscalização por video

#equipe da RTP: 
    #5 servidores + gerente: tratamento das informações
    #equipe de regulação tarifária: 4 servidores economistas + 1 
 
#equipe de fiscalização economica: ao longo do ciclo (5 a 6 pessoas)

#20/21 pessoas no total
 
 
        

#PROCEDIMENTOS ADOTADOS PARA AJUSTE DAS KEYS DEFEITUOSAS:
#banco_v0 = substitui_valor(banco_v0, 43, 'ELGÍVEIS', 'ELEGÍVEIS')
# =============================================================================
# banco_v0 = substitui_valor(banco_v0, 80, 'LEGALIZADO', 'Legalizado')
# 
# banco_v0 = (banco_v0, 107, 'VALORADO SEM VISTORIA', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = (banco_v0, 107, 'VALORADOS SEM VISTORI', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = (banco_v0, 107, 'VALORADOS SEM VISTOR', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = substitui_valor(banco_v0, 107, 'VALORADOS SEM VISTORIAA', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = substitui_valor(banco_v0, 107, 'VALORADO SEM VISTORI', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = substitui_valor(banco_v0, 107, 'VALORADO SEM VISTOR', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = substitui_valor(banco_v0, 107, 'VALORADOS SEM VISTO', 'VALORADOS SEM VISTORIA')
# 
# banco_v0 = substitui_valor(banco_v0, 107, 'VAaLORADOS SEM VISTORI', 'VALORADOS SEM VISTORIA')
# =============================================================================
# =============================================================================
# banco_v0 = substitui_valor(banco_v0, 118, 'LEGALIZADO', 'Legalizado')
# banco_v0 = substitui_valor(banco_v0, 118, '-', 'Campo vazio')
# =============================================================================


#mask = (nao_elegiveis.iloc[:,73] != 0)
#ativos_valid = nao_elegiveis[mask]
#nao_elegiveis.loc[:,'Dep x IA'] = nao_elegiveis.iloc[:, 70]
#nao_elegiveis.loc[mask, 'Dep x IA'] = ativos_valid.iloc[:, 70]*ativos_valid.iloc[:, 73]/100
#formats2(nao_elegiveis['Dep x IA'].sum())
#agrupa(nao_elegiveis, [43, 45, 46], 142, 1, 1)


def calcula_base_contabil(banco):

    #Procedimento para obter a base contabil
    #Calcular a taxa de depreciação contábil em meses
    banco.loc[:,'Taxa Dep contábil [% a.m.] - 1ª RTP'] = 1/banco.iloc[:,47]*100
    mask = (banco.loc[:,'Taxa Dep contábil [% a.m.] - 1ª RTP'] == np.inf)
    banco.loc[mask,'Taxa Dep contábil [% a.m.] - 1ª RTP'] = 0
    
    #Calcular a depreciação acumulada contábil
    mask = (banco.loc[:,'Vida útil consumida - 1ª RTP'] == 'Campo vazio - 1ª RTP')
    banco.loc[mask, 'Vida útil consumida - 1ª RTP'] = 0
    banco.loc[:,'DEP. ACUM. CONTABIL - 1ª RTP (%)'] = banco.loc[:,'Vida útil consumida - 1ª RTP']*banco.loc[:,'Taxa Dep contábil [% a.m.] - 1ª RTP']
    banco.loc[:,'DEP. ACUM. CONTABIL - 1ª RTP (R$)'] = banco.iloc[:,62]*banco.loc[:,'DEP. ACUM. CONTABIL - 1ª RTP (%)']/100
    
    #Atualiza VMU com base no valor contábil
    banco.loc[:, 'VMU CONTABIL - 1ª RTP (R$)'] = banco.iloc[:, 62] - banco.loc[:,'DEP. ACUM. CONTABIL - 1ª RTP (R$)'] + banco.iloc[:,81]
    mask = (banco.iloc[:,73] == 0)
    banco.loc[mask, '53 - ÍNDICE DE APROVEITAMENTO - IA (%)'] = 100
    banco.loc[:, 'VMU CONTABIL x IA - 1ª RTP (R$)'] = banco.loc[:, 'VMU CONTABIL - 1ª RTP (R$)']*banco.iloc[:,73]/100
    
    #Atualizar o valor dos ativos 100% depreciados (limiter)
    mask = (banco.loc[:,'DEP. ACUM. CONTABIL - 1ª RTP (%)'] >= 100)
    banco.loc[mask,'DEP. ACUM. CONTABIL - 1ª RTP (%)'] = 100
    
    #Separar os ativos 100% depreciados pela regra contabil (1ª RTP)
    ativos, baixados = baixa_ativos(banco, 163)   
    
    #Calcula bar bruta
    bar_bruta(banco, 19, 22, 43, 62, 73, 81, 163, 140, 1)
    #Calcula bar liquida
    bar_liquida(banco, 19, 55, 43, 62, 73, 81, 163, 164, 140, 166, 0, 1)
    #Calcula taxa média de depreciação
    calcula_taxa_dep_media(banco, 163, 162)

    #Atualiza valores para a 2ª RTP
    #Calcular a depreciação acumulada contábil
    mask = (banco.loc[:,'Vida útil consumida - 2ª RTP'] == 'Campo vazio - 1ª RTP')
    banco.loc[mask, 'Vida útil consumida - 2ª RTP'] = 0
    banco.loc[:,'DEP. ACUM. CONTABIL - 2ª RTP (%)'] = banco.iloc[:,148]*banco.loc[:,'Taxa Dep contábil [% a.m.] - 1ª RTP']
    mask = (banco.loc[:,'DEP. ACUM. CONTABIL - 2ª RTP (%)'] >= 100)
    banco.loc[mask,'DEP. ACUM. CONTABIL - 2ª RTP (%)'] = 100
    banco.loc[:,'DEP. ACUM. CONTABIL - 2ª RTP (R$)'] = banco.iloc[:,62]*banco.loc[:,'DEP. ACUM. CONTABIL - 2ª RTP (%)']/100
    #Calcular o VMU contabil
    banco.loc[:, 'VMU CONTABIL - 2ª RTP (R$)'] = banco.iloc[:, 62] - banco.loc[:,'DEP. ACUM. CONTABIL - 2ª RTP (R$)'] + banco.iloc[:,81]
    banco.loc[:, 'VMU CONTABIL x IA - 2ª RTP (R$)'] = banco.loc[:, 'VMU CONTABIL - 2ª RTP (R$)']*banco.iloc[:,73]/100
        
    #Calcular valores atualizados pelo IPCA
    banco.loc[:,'DEP. ACUM. CONTABIL [IPCA] - 2ª RTP (R$)'] = banco.loc[:,'DEP. ACUM. CONTABIL - 2ª RTP (R$)']*banco.loc[:,'Variação do IPCA - 2ª RTP']
    banco.loc[:,'VMU CONTABIL [IPCA] - 2ª RTP (R$)'] = banco.loc[:,'VMU CONTABIL - 2ª RTP (R$)']*banco.loc[:,'Variação do IPCA - 2ª RTP']
    banco.loc[:,'VMU CONTABIL x IA [IPCA] - 2ª RTP (R$)'] = banco.loc[:,'VMU CONTABIL x IA - 2ª RTP (R$)']*banco.loc[:,'Variação do IPCA - 2ª RTP']
    
    #Calcula bar bruta
    bar_bruta(banco, 19, 22, 43, 157, 151, 158, 167, 140, 1)
    #Calcula bar liquida
    bar_liquida(banco, 19, 55, 43, 157, 151, 158, 167, 164, 140, 173, 0, 1)
    #Calcula taxa média de depreciação
    calcula_taxa_dep_media(banco, 167, 162)
    
    #bar_liquida(dados_atualizados, i_categoria, 55, 43, 157, 151, 158, 149, 159, 140, 161, 0, 1)

    return

#__________________________________________________Script XX__________________________________________________
def importa_incremental(path):
    #importa o arquivo com a base incremental
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\Anexo_3_BASE_INCREMENTAL_092020.txt'
    
    adicoes = pd.read_csv(path, sep=";", index_col=False, error_bad_lines=False, engine='python')
    
    soma_nan = adicoes.iloc[len(adicoes.index)-1,:].isnull().sum()
    
    #Verifica se a quantidade de NaN da ultima linha é maior que o limite:
    if soma_nan >= 20:
        #Remove a ultima linha
        adicoes = adicoes.iloc[0:len(adicoes.index)-2,:]

    return adicoes
#--------------------------------------------------Script XX--------------------------------------------------

#__________________________________________________Script XX__________________________________________________
def trata_incremental(database):
    #trata os dados de colunas específicas
    
    #Transforma as strings de números
    #Converte para o formato decimal do pandas
    colunas = [26, 27, 29, 30, 31, 32, 33]
    for i in colunas:
       #Ajusta o formato do dado 
        #Converte "," para "."
        database.iloc[:,i] = database.iloc[:,i].map(formats5)
        #Converte string para float
        database.iloc[:,i] = database.iloc[:,i].map(float)

    return database
#--------------------------------------------------Script XX--------------------------------------------------

#__________________________________________________Script XX__________________________________________________
def agrupa2(database, i_colunas_agrupamento, i_coluna_agregacao, ordem_decrescente, formatar):
    #Agrupa os dados por uma coluna específica e retorna as colunas selecionadas
    
    tam = len(i_colunas_agrupamento)
    #Constroi o filtro de colunas de agrupamento dinamicamente
    colunas_agrupamento = '['
    for i in i_colunas_agrupamento:
        if len(i_colunas_agrupamento) > 1 and i != i_colunas_agrupamento[len(i_colunas_agrupamento)-1]:
            colunas_agrupamento = colunas_agrupamento + "database.columns[" + str(i) + '], '
        else:
            colunas_agrupamento = colunas_agrupamento + "database.columns[" + str(i) + ']'
    colunas_agrupamento = colunas_agrupamento + ']'
    
    #Constroi o comando para agrupamento:
    comando_agrup = "database.groupby(" + colunas_agrupamento + ")[database.columns[i_coluna_agregacao]].sum().reset_index(name=database.columns[i_coluna_agregacao])"
    df_agrupado = eval(comando_agrup)
    
    if ordem_decrescente == 1:
        df_agrupado = df_agrupado.sort_values(database.columns[i_coluna_agregacao], ascending=False).reset_index(drop=True)
        
    #Calcula o percentual
    df_agrupado.loc[:,'%'] = df_agrupado.iloc[:,tam]/df_agrupado.iloc[:,tam].sum()
    #Calcula o acumulado
    df_agrupado.loc[:,'Acumulado'] = df_agrupado.iloc[:,tam+1].cumsum()
        
    if formatar == 1:
        #Formata como dinheiro
        df_agrupado.iloc[:,tam] = df_agrupado.iloc[:,tam].apply(formats2)
        #Formata os percentuais
        df_agrupado.iloc[:,tam+1] = df_agrupado.iloc[:,tam+1].apply(formats3)
        df_agrupado.iloc[:,tam+2] = df_agrupado.iloc[:,tam+2].apply(formats3)

    return df_agrupado
#--------------------------------------------------Script XX--------------------------------------------------
def insere_plano_contas2(database, indice_conta_contabil, df_plano_contas, nome_plano):
    #Insere o plano de contas no final do dataframe
    # Indice conta contabil: 86
    
    aux = database.copy()
   
    #Cria a nova coluna no final do dataframe copiando a coluna com os codigos contabeis
    aux[nome_plano] = aux.iloc[:, indice_conta_contabil]

    #Varre o dataframe na coluna indicada, alimentando a coluna do plano de contas fazendo a correspondencia com a tabela do plano de contas
    for i in range(0, len(df_plano_contas)):
        #Procura na coluna de referencia o codigo
        mask = (aux.loc[:,nome_plano] == df_plano_contas.iloc[i, 0])
        #Substitui pelo valor de correspondencia
        aux.loc[mask,nome_plano] = df_plano_contas.iloc[i, 1]

    return aux
#--------------------------------------------------Script 27--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def importa_maringa(path):
    #Importa a lista de ativos não onerosos de maringa conforme TA 21/2019
    #path = 'C:\\Users\\cecil.skaleski\\Documents\\Homeoffice - Cecil\\SANEAMENTO\\RTP e IRT\\BAR\\ATIVOS_NAO_ONEROSOS_MARINGA\\Anexo_2_dataframe.xlsx'
    
    ativos_maringa = pd.read_excel(path, sheet_name=0, skiprows=([0, 1, 2]))
    
    #Remove NaN/NaT
    ativos_maringa = ativos_maringa.dropna(how='all')
    ativos_maringa.index = np.arange(1, len(ativos_maringa)+1)
    
    #Remove a ultima linha
    ativos_maringa = ativos_maringa.head(len(ativos_maringa)-1)
    
    return ativos_maringa
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def carrega_inc():
    #Carrega os ativos da base incremental
    path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\Adicoes 2016\\DB_adicoes_2016_consolidado_plano_contas.h5'
    adic = importa_dados(path)
    path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\BAR_incremental.h5'
    inc = importa_dados(path)
    return adic, inc
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def separa_inc():
    #Separa os ativos da base incremental
    path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\BAR_incremental_filtrada.h5'
    base_inc = importa_dados(path)

    base_virt = base_inc[(base_inc.loc[:, 'Conta Contábil (Descrição)'] == 'Tubulações') | (base_inc.loc[:, 'Conta Contábil (Descrição)'] == 'Ligações Prediais') | (base_inc.loc[:, 'Conta Contábil (Descrição)'] == 'Hidrômetros') | (base_inc.loc[:, 'Conta Contábil (Descrição)'] == 'Macromedidores')]
    print(agrupa(base_virt, [49], 30, 1, 1))
    base_fis = base_inc[(base_inc.loc[:, 'Conta Contábil (Descrição)'] != 'Tubulações') & (base_inc.loc[:, 'Conta Contábil (Descrição)'] != 'Ligações Prediais') & (base_inc.loc[:, 'Conta Contábil (Descrição)'] != 'Hidrômetros') & (base_inc.loc[:, 'Conta Contábil (Descrição)'] != 'Macromedidores')]
    print(agrupa(base_fis, [49], 30, 1, 1))
    return base_virt, base_fis
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def pareto_fast(df_base, formata1, formata2):
    #Faz o pareto dos itens de maior relevancia utilizando a última coluna com a opção de formatar os dados de saída (formata1: percentuais; formata2: valores financeiros)
    
    df = df_base.copy()
    last_column =  df.columns[-1]
    
    df['%'] = df.loc[:, last_column]/df.loc[:, last_column].sum()
    #Ordena pelos maiores percentuais
    df = df.sort_values('%', ascending=False).reset_index(drop=True)
    df['acum'] = df.loc[:, last_column].cumsum()
    df['%_acum'] = df.loc[:, '%'].cumsum()
    if formata1 == True:
        df.loc[:, '%'] = df.loc[:, '%'].apply(formats3)
        df.loc[:, '%_acum'] = df.loc[:, '%_acum'].apply(formats3)
        df.loc[:, '%'] = df.loc[:, '%'].apply(formats6)
        df.loc[:, '%_acum'] = df.loc[:, '%_acum'].apply(formats6)
    if formata2 == True:
        df.loc[:, last_column] = df.loc[:, last_column].apply(formats2)
        df.loc[:, 'acum'] = df.loc[:, 'acum'].apply(formats2)
    return df   
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def filtra_sorteio():
    #Procedimento para filtrar ativos sorteados na base incremental
    
    #Carrega os bancos
    path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\Adicoes 2016\\DB_adicoes_2016_consolidado_plano_contas.h5'
    adic = importa_dados(path)
    path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\SANEAMENTO\RTP e IRT\BAR\BAR_INCREMENTAL_SANEPAR_25_11_2020\BAR_incremental.h5'
    inc = importa_dados(path)
    #Carrega lista de municipios sorteados
    path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Sorteio amostral\Lista_municipios_sorteados.xlsx'
    df_sort = carrega_excel(path)
    lista_sort = df_sort.Municipio.to_list()
    #Inclui ADM na lista
    lista_sort.append('ADMINISTRACAO')
    #Filtra as adições
    adic_sort = adic[adic.iloc[:,15].isin(lista_sort)]
    #Verifica
    result = adic_sort.iloc[:, 15].unique()
    print('Lista de municípios não encontrados nas adições 2016: ')
    for i in lista_sort:
        if i not in (result):
            print(i)
    #Filtra a BAR incremental (2017-2020)
    inc_sort = inc[inc.iloc[:,16].isin(lista_sort)]
    #Verifica
    result = inc_sort.iloc[:, 16].unique()
    print('Lista de municípios não encontrados na BAR incremental: ')
    for i in lista_sort:
        if i not in (result):
            print(i)
    return adic_sort, inc_sort
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def filtra_rede(adic_sort, inc_sort):
    #Procedimento para filtrar ativos de rede sorteados na base incremental
    adic_sort_rede = adic_sort[adic_sort.loc[:, 'Conta Contábil (Descrição)'].isin(['Tubulações', 'Ligações Prediais', 'Hidrômetros'])]
    inc_sort_rede = inc_sort[inc_sort.loc[:, 'Conta Contábil (Descrição)'].isin(['Tubulações', 'Ligações Prediais', 'Hidrômetros'])]
    return adic_sort_rede, inc_sort_rede
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def detalha_tub(adic_sort, inc_sort):
    #Procedimento para detalhar ativos sorteados na base incremental referentes à Tubulações
    #Tubulações
    inc_sort_tub = filtra_coluna(inc_sort, 49, 'Tubulações', '==')
    adic_sort_tub = filtra_coluna(adic_sort, 35, 'Tubulações', '==')
    #Cria paretos
    aux_adic = agrupa(adic_sort_tub, [21], 28, 1, 0)
    aux_inc = agrupa(inc_sort_tub, [22], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_tub = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_tub = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_tub.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_tub.xlsx')
    par_inc_tub.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_tub.xlsx')
    return par_adic_tub, par_inc_tub
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def detalha_hidro(adic_sort, inc_sort):
    #Procedimento para detalhar ativos sorteados na base incremental referentes à Tubulações
    #Hidrômetros
    inc_sort_hid = filtra_coluna(inc_sort, 49, 'Hidrômetros', '==')
    adic_sort_hid = filtra_coluna(adic_sort, 35, 'Hidrômetros', '==')
    #Cria paretos
    aux_adic = agrupa(adic_sort_hid, [21], 28, 1, 0)
    aux_inc = agrupa(inc_sort_hid, [22], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_hid = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_hid = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_hid.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_hid.xlsx')
    par_inc_hid.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_hid.xlsx')
    return par_adic_hid, par_inc_hid
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def detalha_lig(adic_sort, inc_sort):
    #Procedimento para detalhar ativos sorteados na base incremental referentes à Ligações Prediais
    #Ligações Prediais
    inc_sort_lig = filtra_coluna(inc_sort, 49, 'Ligações Prediais', '==')
    adic_sort_lig = filtra_coluna(adic_sort, 35, 'Ligações Prediais', '==')
    #Cria paretos
    aux_adic = agrupa(adic_sort_lig, [21], 28, 1, 0)
    aux_inc = agrupa(inc_sort_lig, [22], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_lig = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_lig = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_lig.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_lig.xlsx')
    par_inc_lig.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_lig.xlsx')
    return par_adic_lig, par_inc_lig
#--------------------------------------------------Script xX--------------------------------------------------





#--------------------------------------------------Script XX--------------------------------------------------
def filtra_demais(adic_sort, inc_sort):
    #Procedimento para filtrar ativos sorteados na base incremental que não são de rede 
    adic_sort_d = adic_sort[~adic_sort.loc[:, 'Conta Contábil (Descrição)'].isin(['Tubulações', 'Ligações Prediais', 'Hidrômetros'])]
    inc_sort_d = inc_sort[~inc_sort.loc[:, 'Conta Contábil (Descrição)'].isin(['Tubulações', 'Ligações Prediais', 'Hidrômetros'])]
    return adic_sort_d, inc_sort_d
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def detalha_demais1(adic_sort_d, inc_sort_d):
    #Procedimento para detalhar ativos sorteados na base incremental que não são de rede 
    #Construções civis
    inc_sort_ccivis = filtra_coluna(inc_sort_d, 49, 'Construções Civis', '==')
    adic_sort_ccivis = filtra_coluna(adic_sort_d, 35, 'Construções Civis', '==')
    #Cria paretos
    aux_adic = agrupa(adic_sort_ccivis, [21], 28, 1, 0)
    aux_inc = agrupa(inc_sort_ccivis, [22], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_ccvis = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_ccvis = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_ccvis.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_ccvis.xlsx')
    par_inc_ccvis.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_ccvis.xlsx')
    return par_adic_ccvis, par_inc_ccvis
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def detalha_demais2(adic_sort_d, inc_sort_d):
    #Procedimento para detalhar ativos sorteados na base incremental que não são de rede 
    #Equipamentos
    inc_sort_equip = filtra_coluna(inc_sort_d, 49, 'Equipamentos', '==')
    adic_sort_equip = filtra_coluna(adic_sort_d, 35, 'Equipamentos', '==')
    #Cria paretos
    aux_adic = agrupa(adic_sort_equip, [21], 28, 1, 0)
    aux_inc = agrupa(inc_sort_equip, [22], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_equip = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_equip = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_equip.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_equip.xlsx')
    par_inc_equip.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_equip.xlsx')
    return par_adic_equip, par_inc_equip
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script XX--------------------------------------------------
def detalha_demais3(adic_sort_d, inc_sort_d):
    #Procedimento para detalhar ativos sorteados na base incremental que não são de rede 
    #Terrenos
    inc_sort_ter = filtra_coluna(inc_sort_d, 49, 'Terrenos', '==')
    adic_sort_ter = filtra_coluna(adic_sort_d, 35, 'Terrenos', '==')
    #Cria paretos
    aux_adic = agrupa(adic_sort_ter, [21], 28, 1, 0)
    aux_inc = agrupa(inc_sort_ter, [22], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_ter = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_ter = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_ter.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_ter.xlsx')
    par_inc_ter.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_ter.xlsx')
    return par_adic_ter, par_inc_ter
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def inc_munic(adic_sort_d, inc_sort_d):
    #Monta pareto da base incremental amostral de campo por município
    #Seleciona as contas contábeis (Construções Civis, Equipamentos e Terrenos)
    adic_sort_campo = adic_sort_d[adic_sort_d.loc[:, 'Conta Contábil (Descrição)'].isin(['Construções Civis', 'Equipamentos', 'Terrenos'])]
    inc_sort_campo = inc_sort_d[inc_sort_d.loc[:, 'Conta Contábil (Descrição)'].isin(['Construções Civis', 'Equipamentos', 'Terrenos'])]
    #Cria paretos
    aux_adic = agrupa(adic_sort_campo, [15], 28, 1, 0)
    aux_inc = agrupa(inc_sort_campo, [16], 30, 1, 0)
    #print("Pareto BAR incremental amostral (2016-2017): ")
    par_adic_munic = pareto_fast(aux_adic, True, True)
    #print("Pareto BAR incremental amostral (2017-2020): ")
    par_inc_munic = pareto_fast(aux_inc, True, True)
    #Exporta excel
    par_adic_munic.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_adic_munic.xlsx')
    par_inc_munic.to_excel(r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\DIagnostico BAR Incremental\Paretos\par_inc_munic.xlsx')
    return par_adic_munic, par_inc_munic
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def dados_rede(base):
    #Extrai o diâmetro e material dos ativos de rede e adicona à base de tubulações
    #Filtra dados de tubulações
    aux_base = base.copy()
    base_rede = filtra_coluna(aux_base, 140, 'Tubulações', '==')
    #Busca as informações de diâmetro do tubo
    #Filtra somente elementos de tubulação (possuem o atributo diâmetro nominal)
    aux_rede = base_rede[base_rede.loc[:, '12 - DESCRIÇÃO DO BEM'].str.contains('DN', na=False)]
    #Separa os diâmetros nominais e material
    dns = []
    mats = []
    for i in aux_rede.loc[:, '12 - DESCRIÇÃO DO BEM'].to_list():
        aux_dn = i.split('DN')[1].strip().split(' ')[0]
        if aux_dn.isdigit() == False:
            aux_dn = 0
        dns.append(int(aux_dn))
        mats.append(i.split('DN')[0].strip())
    #Adiciona no DataFrame
    aux_rede['DN'] = dns
    aux_rede['Material'] = mats
    return aux_rede
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def vnr_linear(base_rede):
    #Calcula o vnr por metro dos ativos de tubulação
    base_rede['VNR_linear [R$/m]'] = base_rede.loc[:, '44 - VALOR NOVO DE REPOSIÇÃO - VNR (R$)']/base_rede.loc[:, '13 - QUANTIDADE']
    #Arredonda os valores para duas casas decimais
    base_rede['VNR_linear [R$/m]'] = base_rede['VNR_linear [R$/m]'].apply(arred2)
    return base_rede
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def vnr_rede(base):
    #Calcula o VNR por metro médio dos ativos de rede para vários tipos de agrupamentos
    #Adiciona e ano de aquisição e o ano de cadastro no sistema contábil
    base_rede = base.copy()
    #Ajusta a nomenclatura
    base_rede.loc[:, 'Material'] =  base_rede.loc[:, 'Material'].str.replace("TUBOS", "TUBO")
    base_rede.loc[:, 'Material'] =  base_rede.loc[:, 'Material'].str.replace("TUBO", "TUBOS")
    ano_aquis = []
    ano_cad = []
    ano_dep = []
    for i in base_rede.index:
        aux = base_rede.loc[i, base_rede.columns[24]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_aquis.append(aux)
        aux = base_rede.loc[i, base_rede.columns[25]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_cad.append(aux)
        aux = base_rede.loc[i, base_rede.columns[49]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_dep.append(aux)
    base_rede['Ano_aquisição'] = ano_aquis
    base_rede['Ano_cadastro_SGP'] = ano_cad
    base_rede['Ano_operação'] = ano_dep
    
    base_group = agrupa(base_rede, [142, 141, 143, 19, 3, 144, 145, 146, 46], 22, 0, 0)
    #Filtra para cada agrupamento printando na tela os resultados
    #Lista os materiais disponíveis
    lista_mat = sorted(base_group.Material.unique())
    #Para cada material, lista os diâmetros disponíveis
    print(' ')
    n = 1
    lista_var = []
    df_all = pd.DataFrame([])
    for mat in lista_mat:
        #if n >= 366:
           #break
        df_mat = base_group[base_group.Material == mat]
        lista_dn = sorted(df_mat.DN.unique())
        for dn in lista_dn:
            #if n >= 366:
                #break
            #Filtra e printa na tela
            aux_df = df_mat[df_mat.DN == dn]
            #Ordena
            aux_df.columns = ['Material', 'DN', 'VNR_linear [R$/m]', 'Serviço', 'Município', 'Ano_aquisição', 'Ano_cadastro_SGP', 'Ano_operação', 'Situação', 'Qtde [m]']
            aux_df = aux_df.sort_values(['VNR_linear [R$/m]', 'Serviço', 'Município', 'Ano_aquisição', 'Situação'], ascending=[False, True, True, True, True]).reset_index(drop=True)
            #Agrupa similares
            linhas = []
            #Mesmo VNR, serviço e município
            #Lista os VNR disponíveis
            aux_vnr = sorted(aux_df.loc[:, 'VNR_linear [R$/m]'].unique())
            for vnr in aux_vnr:
               #Para cada VNR, lista os serviços disponíveis
               df_vnr = aux_df[aux_df.loc[:, 'VNR_linear [R$/m]'] == vnr]
               aux_serv = sorted(df_vnr.loc[:, 'Serviço'].unique())
               #Para cada serviço, lista os Municípios disponíveis
               for serv in aux_serv:
                   df_serv = df_vnr[df_vnr.loc[:, 'Serviço'] == serv]
                   aux_mun = sorted(df_serv.loc[:, 'Município'].unique())
                   #Para cada município, avalia a situação do inventário
                   for mun in aux_mun:
                       df_mun = df_serv[df_serv.loc[:, 'Município'] == mun]
                       aux_inv = sorted(df_mun.loc[:, 'Situação'].unique())
                       #Para cada situação de inventário, avalia as datas de imobilização e estabelece um range, se houver
                       for inv in aux_inv:
                           df_inv = df_mun[df_mun.loc[:, 'Situação'] == inv]
                           min_a = df_inv.loc[:, 'Ano_aquisição'].min()
                           max_a = df_inv.loc[:, 'Ano_aquisição'].max()
                           if min_a != max_a:
                               aux_a = min_a + ' a ' + max_a
                           else:
                               aux_a = min_a
                           min_c = df_inv.loc[:, 'Ano_cadastro_SGP'].min()
                           max_c = df_inv.loc[:, 'Ano_cadastro_SGP'].max()
                           if min_c != max_c:
                               aux_c = min_c + ' a '+  max_c
                           else:
                               aux_c = min_c
                           min_o = df_inv.loc[:, 'Ano_operação'].min()
                           max_o = df_inv.loc[:, 'Ano_operação'].max()
                           if min_o != max_o:
                               aux_o = min_o + ' a '+  max_o
                           else:
                               aux_o = min_o
                           #Soma as extensões de rede similares
                           soma_qtde = df_inv.loc[:, 'Qtde [m]'].sum()
                           linhas.append([mat, dn, vnr, serv, mun, aux_a, aux_c, aux_o, inv, soma_qtde])
            #Monta o dataframe
            aux_df2 = pd.DataFrame(linhas)
            aux_df2.columns = aux_df.columns
            #Ordena
            aux_df2 = aux_df2.sort_values(['VNR_linear [R$/m]', 'Serviço', 'Município', 'Situação'], ascending=[False, True, True, True]).reset_index(drop=True)
            #Printa
            print(str(n) + '._______________________________' + mat + ' ' + str(dn) + 'MM' + '_______________________________')
            print(aux_df2)
            print('_______________________________'+'_______________________________')
            print(' ')
            #Lista de todas as variações existentes
            lista_var.append(mat + ' ' + str(dn) + 'MM')
            #Concatena os dataframes
            df_all = df_all.append(aux_df2, ignore_index=True)
            #if n >= 366:
                #break
            n = n + 1
    return base_rede, base_group, lista_var, df_all
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def iq_rede(dados_sobra, dados_conc):
    #Calcula o indicador de qualidade do processo de imobilização dos ativos de rede
    dados_sobra = base_rede_sobra2.Ano_aquisição.apply(int)
    dados_conc = base_rede_conc2.Ano_aquisição.apply(int)
    #Calcula o range de valores
    range_sobra = list(dados_sobra.unique())
    range_conc =list(dados_conc.unique())
    range_all = sorted(list(set(range_sobra+range_conc)))
    #Define a quantidade de bins
    bins = len(range_all)
    range_bins = sorted(list(set(np.linspace(range_all[0], range_all[-1], bins, dtype=int))))
    #Para cada ano, calcula a frequencia de sobras contábeis e ativos conciliados
    freqs_sobras = []
    freqs_conc = []
    list_sobra = dados_sobra.to_list()
    list_conc = dados_conc.to_list()
    for ano in range_bins:
        freqs_sobras.append(list_sobra.count(ano))
        freqs_conc.append(list_conc.count(ano))
    #Calcula o indicador em cada ano
    iq = np.array(freqs_sobras)/(np.array(freqs_conc)+np.array(freqs_sobras))
    #Normaliza os vetores de dados
    freqs_sobras_norm = np.array(freqs_sobras)/(sum(freqs_sobras)+sum(freqs_conc))*100
    freqs_conc_norm = np.array(freqs_conc)/(sum(freqs_sobras)+sum(freqs_conc))*100
    #Plota os dados
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(10,10))
    plt.bar(range_bins, freqs_sobras_norm, color='crimson', label='Sobras contábeis', width=0.8, alpha=0.5, zorder=2)
    plt.bar(range_bins, freqs_conc_norm, color='blue', label='Ativos conciliados', width=0.8, alpha=0.5)
    plt.plot(range_bins, iq, color='darkorange', label='iq - Sobras/Conciliados',alpha=0.8, zorder=10)
    plt.xticks(range_bins, rotation=90)
    plt.legend(loc='best')
    plt.ylabel('Percentual do total de ativos de rede imobilizados (BAR) [%]')
    plt.title('Processo de imobilização de ativos de rede - BAR')
    plt.show()
    return
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def iq_bar(df_base):
    #Calcula o indicador de qualidade do processo de imobilização dos ativos
    base = df_base.copy()
    #Filtra os campos vazios
    base = base[base.loc[:, base.columns[24]] != 'Campo vazio']
    ano_aquis = []
    ano_cad = []
    ano_dep = []
    for i in base.index:
        aux = base.loc[i, base.columns[24]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_aquis.append(aux)
        aux = base.loc[i, base.columns[25]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_cad.append(aux)
        aux = base.loc[i, base.columns[49]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_dep.append(aux)
    base['Ano_aquisição'] = ano_aquis
    base['Ano_cadastro_SGP'] = ano_cad
    base['Ano_operação'] = ano_dep
    #Separa em sobras contábeis e ativos conciliados
    
    dados_sobra = filtra_coluna(base, 46, 'CONCILIADO', '!=').Ano_aquisição.apply(int)
    dados_conc = filtra_coluna(base, 46, 'CONCILIADO', '==').Ano_aquisição.apply(int)
    #Calcula o range de valores
    range_sobra = list(dados_sobra.unique())
    range_conc =list(dados_conc.unique())
    range_all = sorted(list(set(range_sobra+range_conc)))
    #Define a quantidade de bins
    bins = len(range_all)
    range_bins = sorted(list(set(np.linspace(range_all[0], range_all[-1], bins, dtype=int))))
    #Para cada ano, calcula a frequencia de sobras contábeis e ativos conciliados
    freqs_sobras = []
    freqs_conc = []
    list_sobra = dados_sobra.to_list()
    list_conc = dados_conc.to_list()
    for ano in range_bins:
        freqs_sobras.append(list_sobra.count(ano))
        freqs_conc.append(list_conc.count(ano))
    #Calcula o indicador em cada ano
    iq = np.array(freqs_sobras)/(np.array(freqs_conc)+np.array(freqs_sobras))
    #Normaliza os vetores de dados
    freqs_sobras_norm = np.array(freqs_sobras)/(sum(freqs_sobras)+sum(freqs_conc))*100
    freqs_conc_norm = np.array(freqs_conc)/(sum(freqs_sobras)+sum(freqs_conc))*100
    #Plota os dados
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(10,10))
    plt.bar(range_bins, freqs_sobras_norm, color='crimson', label='Sobras contábeis', width=0.8, alpha=0.5, zorder=2)
    plt.bar(range_bins, freqs_conc_norm, color='blue', label='Ativos conciliados', width=0.8, alpha=0.5)
    plt.plot(range_bins, iq, color='darkorange', label='iq - Sobras/Conciliados',alpha=0.8, zorder=10)
    plt.xticks(range_bins, rotation=90)
    plt.legend(loc='best')
    plt.ylabel('Percentual do total de ativos imobilizados (BAR) [%]')
    plt.title('Processo de imobilização de ativos - BAR')
    plt.show()
    return
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def iq_bar_cc(df_base, plota):
    #Calcula o indicador de qualidade do processo de imobilização dos ativos por conta contábil
    base = df_base.copy()
    #Filtra os campos vazios
    base = base[base.loc[:, base.columns[24]] != 'Campo vazio']
    ano_aquis = []
    ano_cad = []
    ano_dep = []
    for i in base.index:
        aux = base.loc[i, base.columns[24]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_aquis.append(aux)
        aux = base.loc[i, base.columns[25]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_cad.append(aux)
        aux = base.loc[i, base.columns[49]]
        if aux != 'Campo vazio':
            aux = aux.split('/')[1]
        ano_dep.append(aux)
    base['Ano_aquisição'] = ano_aquis
    base['Ano_cadastro_SGP'] = ano_cad
    base['Ano_operação'] = ano_dep

    #Separa em sobras contábeis e ativos conciliados
    iqs = []
    anos = []
    last_iqs = []
    last_anos = []
    vnr_concs = []
    print(' ')
    contas = sorted(list(base.loc[:, 'Conta Contábil (Descrição)'].unique()))
    for conta in contas:
        base_aux = base[base.loc[:, 'Conta Contábil (Descrição)'] == conta]
        dados_sobra = filtra_coluna(base_aux, 46, 'CONCILIADO', '!=').Ano_aquisição.apply(int)
        dados_conc = filtra_coluna(base_aux, 46, 'CONCILIADO', '==').Ano_aquisição.apply(int)
        #Calcula o range de valores
        range_sobra = list(dados_sobra.unique())
        range_conc =list(dados_conc.unique())
        range_all = sorted(list(set(range_sobra+range_conc)))
        #Define a quantidade de bins
        bins = len(range_all)
        range_bins = sorted(list(set(np.linspace(range_all[0], range_all[-1], bins, dtype=int))))
        #Para cada ano, calcula a frequencia de sobras contábeis e ativos conciliados
        freqs_sobras = []
        freqs_conc = []
        list_sobra = dados_sobra.to_list()
        list_conc = dados_conc.to_list()
        for ano in range_bins:
            freqs_sobras.append(list_sobra.count(ano))
            freqs_conc.append(list_conc.count(ano))
        #Calcula o indicador em cada ano
        iq = np.array(freqs_sobras)/(np.array(freqs_conc)+np.array(freqs_sobras))
        #Normaliza os vetores de dados
        freqs_sobras_norm = np.array(freqs_sobras)/(sum(freqs_sobras)+sum(freqs_conc))*100
        freqs_conc_norm = np.array(freqs_conc)/(sum(freqs_sobras)+sum(freqs_conc))*100
        iqs.append(iq)
        last_iqs.append(iq[-1]*100)
        last_anos.append(range_bins[-1])
        anos.append(range_bins)
        #Printa o ultimo valor do indicador
        print(conta + ': ' + formats3(iq[-1]/100))
        if plota == True:
            #Plota os dados
            fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(10,10))
            plt.bar(range_bins, freqs_sobras_norm, color='crimson', label='Sobras contábeis', width=0.8, alpha=0.5, zorder=2)
            plt.bar(range_bins, freqs_conc_norm, color='blue', label='Ativos conciliados', width=0.8, alpha=0.5)
            plt.plot(range_bins, iq, color='darkorange', label='iq - Sobras/Conciliados',alpha=0.8, zorder=10)
            plt.xticks(range_bins, rotation=90)
            plt.legend(loc='best')
            plt.ylabel('Percentual do total de ativos imobilizados - ' + conta + ' (BAR) [%]')
            plt.title('Processo de imobilização de ativos - ' + conta + ' (BAR)')
            plt.show()
    #Monta o dataframe com o histórico dos indicadores de imobilização
    df_iq = pd.DataFrame({
        'Conta contábil': contas,
        'Iq [%]': last_iqs,
        'Ano': last_anos,
        'Anos': anos,
        'IQs': iqs
        })
    df_iq = df_iq.sort_values('Iq [%]', ascending=False).reset_index(drop=True)
    return df_iq
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def conta_termos(base_descr):
    #Calcula a frequência de ocorrência dos termos na descrição dos ativos
    lista_base = base_descr.to_list()
    #Divide em substrings
    lista_geral = []
    for i in lista_base:
        aux = i.split(' ')
        lista_geral = lista_geral + aux
    #Gera a lista de termos únicos
    lista_uniq = list(set(lista_geral))
    #Remove espaço vazio
    lista_uniq = [x for x in lista_uniq if x != '']
    #Para cada elemento, contabiliza a frequência e ordem mediana no texto
    freqs = []
    med_ordem = []
    for termo in lista_uniq:
        freqs.append(lista_geral.count(termo))
        pos = []
        #Filtra as linhas em que ocorrem o termo em análise
        aux_filt = base_descr[base_descr.str.contains(termo, regex=False)].to_list()
        for linha in aux_filt:
            #Separa os elementos 
            aux_linha = linha.split(' ')
            #Verifica se o elemento está na lista
            aux_count = aux_linha.count(termo)
            if aux_count > 0:
                #Busca a posição do termo
                pos.append(aux_linha.index(termo))
        #Calcula a mediana da posição
        med_ordem.append(np.median(pos))
    #Monta o dataframe
    df_termos = pd.DataFrame({
        'Termo': lista_uniq,
        'Posição': med_ordem,
        'Frequência': freqs
        })
    #Oganiza
    df_termos = df_termos.sort_values(['Posição', 'Frequência', 'Termo'], ascending=[True, False, True]).reset_index(drop=True)
    return df_termos
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def conta_termos2(base_descr):
    #Calcula a frequência de ocorrência dos 1ºos termos na descrição dos ativos
    lista_base = base_descr.to_list()
    #Divide em substrings
    lista_geral = []
    for i in lista_base:
        aux = i.split(' ')[0]
        lista_geral.append(aux)
    #Gera a lista de termos únicos
    lista_uniq = sorted(list(set(lista_geral)))
    #Remove espaço vazio
    lista_uniq = [x for x in lista_uniq if x != '']
    #Para cada elemento, busca os próximos elementos e contabiliza a frequência
    freqs = []
    cats = []
    for termo in lista_uniq:
        #Filtra as linhas em que ocorrem o termo em análise
        aux_filt = base_descr[base_descr.str.contains(termo, regex=False)].to_list()
        for linha in aux_filt:
            #Separa os elementos 
            aux_linha = linha.split(' ')
            if len(aux_linha) > 1:
                #Verifica se o elemento está na lista
                aux_count = aux_linha.count(termo)
                if aux_count > 0:
                    #Busca a posição do termo
                    aux_pos = aux_linha.index(termo)
                    if aux_pos == 0:
                        #Anota o termo seguinte
                        aux_elem1 = aux_linha[aux_pos+1]
                        if len(aux_linha) > 2:
                            #Anota o termo seguinte
                            aux_elem2 = aux_linha[aux_pos+2]
                        else:
                            aux_elem2 = ''
                        cats.append([termo, aux_elem1, aux_elem2])
    #Monta o dataframe        
    df_categ = pd.DataFrame(cats)
    df_categ.columns = ['CAT1', 'CAT2', 'CAT3']
    return df_categ
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def tokeniza(base_descr):
    #Tokeniza as frases descritivas de cada ativo
    lista_base = base_descr.to_list()
    #Divide em substrings
    lista_geral = []
    for i in lista_base:
        #Força string
        aux = str(i).split(' ')
        lista_geral.append(aux)
    lista_exclusao = ['DE', 'DA', 'DO', 'EM', 'PARA', 'NOS', 'NAS', 'E', '']
    lista_token = []
    for frase in lista_geral:
        #Elimina numerais do início da frase
        if frase[0].isnumeric():
            aux = frase[1::]
        else:
            aux = frase
        #Analisa quanto à lista de exclusao e elementos unitários
        aux2 = [x for x in aux if x not in lista_exclusao and len(x) > 1]
        lista_token.append(aux2)
    
    #Cria o DataFrame
    df_token = pd.DataFrame(lista_token)
    #Agrupa e ordena
    df_token_cat1 = df_token.groupby([0]).size().reset_index(name='Qtde').sort_values('Qtde', ascending=False).reset_index(drop=True)
    df_token_cat1.columns = ['Categoria', 'Qtde']
    df_token_cat1['Qtde [%]'] = df_token_cat1.loc[:, 'Qtde']/df_token_cat1.loc[:, 'Qtde'].sum()*100
    #print(df_token_cat1.head(30))
    return df_token, df_token_cat1
#--------------------------------------------------Script xX--------------------------------------------------


#--------------------------------------------------Script xX--------------------------------------------------
def tokeniza2(base, indice_descr, indice_qtde, indice_custo, indice_serv, indice_local, indice_aquis, indice_conta):
    #Tokeniza as frases descritivas de cada ativo e coleta os seguintes dados:
    #Descrição do bem, Quantidade, VNR/CCV ou CC, Serviço prestado, Município, Data de aquisição, Conta contábil
    lista_descr = base.iloc[:, indice_descr].to_list()
    lista_custo = base.iloc[:, indice_custo].to_list()
    lista_qtde = base.iloc[:, indice_qtde].to_list()
    lista_serv = base.iloc[:, indice_serv].to_list()
    lista_loc = base.iloc[:, indice_local].to_list()
    lista_aquis = base.iloc[:, indice_aquis].to_list()
    lista_conta = base.iloc[:, indice_conta].to_list()
    
    #Calcula o custo unitário de cada elemento
    lista_custo_un = np.array(lista_custo)/np.array(lista_qtde)

    #Divide em substrings
    lista_geral = []
    for i in lista_descr:
        #Força string
        aux = str(i).split(' ')
        lista_geral.append(aux)
    lista_exclusao = ['DE', 'DA', 'DO', 'EM', 'PARA', 'NOS', 'NAS', 'E', '']
    lista_token = []
    for frase in lista_geral:
        #Elimina numerais do início da frase
        if frase[0].isnumeric():
            aux = frase[1::]
        else:
            aux = frase
        #Analisa quanto à lista de exclusao e elementos unitários
        aux2 = [x for x in aux if x not in lista_exclusao and len(x) > 1]
        lista_token.append(aux2)
    
    #Cria o DataFrame tokenizado
    df_token = pd.DataFrame(lista_token)
    #Adiciona colunas de dados regulatórios
    df_token['Custo_unit'] = lista_custo_un
    df_token['Localidade'] = lista_loc
    df_token['Serviço'] = lista_serv
    df_token['Data_aquis'] = lista_aquis
    df_token['Conta'] = lista_conta
    
    #Agrupa e ordena
    df_token_cat1 = df_token.groupby([0]).size().reset_index(name='Qtde').sort_values('Qtde', ascending=False).reset_index(drop=True)
    df_token_cat1.columns = ['Categoria', 'Qtde']
    df_token_cat1['Qtde [%]'] = df_token_cat1.loc[:, 'Qtde']/df_token_cat1.loc[:, 'Qtde'].sum()*100
    #print(df_token_cat1.head(30))
    return df_token, df_token_cat1
#--------------------------------------------------Script xX--------------------------------------------------


#--------------------------------------------------Script xX--------------------------------------------------
def analisa_match(lista_words, thresh):
    #Analisa a similaridade entre cada elemento da lista, apresenta o dataframe com os resultados limitando pela menor média dos indicadores
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process
    #Calcula os índices
    a = []
    b = []
    simple_ratios = []
    partial_ratios = []
    token_sort_ratios = []
    token_set_ratios = []
    mean_ratios = []
    median_ratios = []
    desv_ratios = []
    lista_elem = list(set(lista_words))
    for elem in lista_elem:
        #Gera lista dos demais elementos excluindo o que está sendo comparado
        lista_comp = [x for x in lista_elem if x != elem]
        for comp in lista_comp:
            a.append(elem)
            b.append(comp)
            aux_simple_ratio = fuzz.ratio(elem, comp)
            aux_partial_ratio = fuzz.partial_ratio(elem, comp)
            aux_sort_ratio = fuzz.token_sort_ratio(elem, comp)
            aux_set_ratio = fuzz.token_set_ratio(elem, comp)
            simple_ratios.append(aux_simple_ratio)
            partial_ratios.append(aux_partial_ratio)
            token_sort_ratios.append(aux_set_ratio)
            token_set_ratios.append(aux_set_ratio)
            mean_ratios.append(np.mean([aux_simple_ratio, aux_partial_ratio, aux_sort_ratio, aux_set_ratio]))
            median_ratios.append(np.median([aux_simple_ratio, aux_partial_ratio, aux_sort_ratio, aux_set_ratio]))
            desv_ratios.append(np.std([aux_simple_ratio, aux_partial_ratio, aux_sort_ratio, aux_set_ratio]))
    #Cria DataFrame
    df_fuzz = pd.DataFrame({
        'Ref': a,
        'Match': b,
        'Simple ratio': simple_ratios,
        'Partial ratio': partial_ratios,
        'Sort ratio': token_sort_ratios,
        'Set ratio': token_set_ratios,
        'mean ratio': mean_ratios,
        'median ratio': median_ratios,
        'desv ratio': desv_ratios,
        })
    #Ordena por maior ratios
    df_fuzz = df_fuzz.sort_values(['mean ratio', 'desv ratio'], ascending=[False, True]).reset_index(drop=True)
    #Filtra
    df_fuzz = df_fuzz[(df_fuzz.loc[:, 'mean ratio'] >= thresh) & (df_fuzz.loc[:, 'Simple ratio'] > thresh)]
    return df_fuzz
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def analisa_match2(lista_words, lista_freqs, thresh):
    #Analisa a similaridade entre cada elemento da lista, apresenta o dataframe com os resultados limitando pela menor média dos indicadores
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process
    #Calcula os índices
    a = []
    freq_a = []
    b = []
    freq_b = []
    simple_ratios = []
    partial_ratios = []
    token_sort_ratios = []
    token_set_ratios = []
    mean_ratios = []
    median_ratios = []
    desv_ratios = []
    df_freqs = pd.DataFrame({'Termo': lista_words, 'Freq': lista_freqs})
    lista_elem = lista_words
    for elem in lista_elem:
        #Gera lista dos demais elementos excluindo o que está sendo comparado
        lista_comp = [x for x in lista_elem if x != elem]
        for comp in lista_comp:
            a.append(elem)
            freq_a.append(df_freqs[df_freqs.Termo == elem].Freq.head(1).iloc[0])
            b.append(comp)
            freq_b.append(df_freqs[df_freqs.Termo == comp].Freq.head(1).iloc[0])
            aux_simple_ratio = fuzz.ratio(elem, comp)
            aux_partial_ratio = fuzz.partial_ratio(elem, comp)
            aux_sort_ratio = fuzz.token_sort_ratio(elem, comp)
            aux_set_ratio = fuzz.token_set_ratio(elem, comp)
            simple_ratios.append(aux_simple_ratio)
            partial_ratios.append(aux_partial_ratio)
            token_sort_ratios.append(aux_set_ratio)
            token_set_ratios.append(aux_set_ratio)
            mean_ratios.append(np.mean([aux_simple_ratio, aux_partial_ratio, aux_sort_ratio, aux_set_ratio]))
            median_ratios.append(np.median([aux_simple_ratio, aux_partial_ratio, aux_sort_ratio, aux_set_ratio]))
            desv_ratios.append(np.std([aux_simple_ratio, aux_partial_ratio, aux_sort_ratio, aux_set_ratio]))
    #Cria DataFrame
    df_fuzz = pd.DataFrame({
        'Ref': a,
        'Freq_ref': freq_a,
        'Match': b,
        'Freq_match': freq_b,
        'Simple ratio': simple_ratios,
        'Partial ratio': partial_ratios,
        'Sort ratio': token_sort_ratios,
        'Set ratio': token_set_ratios,
        'mean ratio': mean_ratios,
        'median ratio': median_ratios,
        'desv ratio': desv_ratios,
        })
    #Ordena por maior ratios
    df_fuzz = df_fuzz.sort_values(['mean ratio', 'desv ratio'], ascending=[False, True]).reset_index(drop=True)
    #Filtra
    df_fuzz = df_fuzz[(df_fuzz.loc[:, 'mean ratio'] >= thresh) & (df_fuzz.loc[:, 'Simple ratio'] > thresh)]
    return df_fuzz
#

#--------------------------------------------------Script xX--------------------------------------------------
def lista_ajustes(base, indice_contas, indice_descricao):
    #Lista as strings identificadas como intercambiaveis em cada conta contabil
    aux_base = base.copy()
    nome_coluna = aux_base.columns[indice_contas]
    for conta in sorted(aux_base.loc[:, nome_coluna].unique()):
        #Tokeniza a coluna com as descrições dos ativos
        df_token, df_token_cat1 = tokeniza(aux_base[aux_base.loc[:, nome_coluna] == conta].iloc[:, indice_descricao])
        print('____________________________________________' + conta + '____________________________________________')
        thresh = 69
        df_fuzz = analisa_match2(df_token_cat1.Categoria.to_list(), df_token_cat1.Qtde.to_list(), thresh)
        print(' ')
        if len(df_fuzz) > 0:
            print(df_fuzz)
        print('____________________________________________' + conta + '____________________________________________')
        print(' ')
    return
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def substitui_string(base, indice_coluna, valor_original, valor_novo):
    #Substitui os valores na coluna indicada (matching exato)
    base_nova = base.copy()
    nome_coluna = base_nova.columns[indice_coluna]
    base_nova.loc[:, nome_coluna] = base_nova.loc[:, nome_coluna].str.replace(' '+valor_original+' ', ' '+valor_novo+' ', regex=True)
    return base_nova
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def avalia_custo_un(df_tokens, niveis):
    #Avalia o custo unitário de cada token de base (até a quantidade de níveis de informação especificada) agregando os atributos comuns
    lista_atrib = ['Conta']
    for i in range(0, niveis):
        lista_atrib.append(i)
    lista_atrib = lista_atrib + ['Serviço', 'Localidade', 'Data_aquis', 'Custo_unit']
    df_group = df_tokens.groupby(by=lista_atrib).size().reset_index(name='Qtde')
    return df_group
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def lista_atrib(df_atrib):
    #Lista os atributos únicos relacionados com um atributo específico
    df_group = avalia_custo_un(df_token, 2)
    df_hidr = df_group[df_group.Conta == 'Hidrômetros']
    a = df_hidr[df_hidr.Custo_unit == 62]
    for i in a.columns:
        print('___________________________________________' + str(i) + '___________________________________________')
        print(sorted(a.loc[:, i].unique()))
        print('___________________________________________' + str(i) + '___________________________________________')
        print(' ')
    return
#--------------------------------------------------Script xX--------------------------------------------------

#--------------------------------------------------Script xX--------------------------------------------------
def importa_tabela_conc(path):
    #Importa e trata a tabela de conciliação de ativos (Laudo SETAPE 2015)
    #path = r'C:\Users\cecil.skaleski\Documents\Homeoffice - Cecil\EM ANALISE_JULHO_2020\_ARQUIVADOS\16.940.766-5 - SANEPAR (Cadastro tecnico e comercial)\Conciliação_Materiais.xlsx'
    #Carrega dados em formato excel
    df_agua = pd.read_excel(path, sheet_name='AGUA', header=[0], dtype=object, engine='openpyxl').dropna(axis=1, how="all")
    df_esgoto = pd.read_excel(path, sheet_name='ESGOTO', header=[0], dtype=object, engine='openpyxl').dropna(axis=1, how="all")
    df_ref = pd.read_excel(path, sheet_name='Referencia', header=[0], dtype=object, engine='openpyxl').dropna(axis=1, how="all")
    df_agua.reset_index(inplace=True, drop=True)
    df_esgoto.reset_index(inplace=True, drop=True)
    df_ref.reset_index(inplace=True, drop=True)
    #Ajusta o nome das colunas
    df_agua.columns = ['Contábil - Material', 'Contábil - DN', 'Cadastro - Material', 'Cadastro - DN', 'Sugestão - Material', 'Sugestão - DN']
    df_esgoto.columns = ['Contábil - Material', 'Contábil - DN', 'Cadastro - Material', 'Cadastro - DN', 'Sugestão - Material', 'Sugestão - DN']
    #Preenche as células mescladas da coluna de sugestão
    df_agua.loc[:, 'Sugestão - Material'] = df_agua.loc[:, 'Sugestão - Material'].fillna(method='ffill')
    df_agua.loc[:, 'Sugestão - DN'] = df_agua.loc[:, 'Sugestão - DN'].fillna(method='ffill')
    df_esgoto.loc[:, 'Sugestão - Material'] = df_esgoto.loc[:, 'Sugestão - Material'].fillna(method='ffill')
    df_esgoto.loc[:, 'Sugestão - DN'] = df_esgoto.loc[:, 'Sugestão - DN'].fillna(method='ffill')
    #Adiciona a coluna de referência para o material do cadastro tecnico
    df_agua = lookup(df_agua, df_ref, 'Cadastro - Material')
    df_esgoto = lookup(df_agua, df_ref, 'Cadastro - Material')
    #Substitui nan por vazio
    df_agua = df_agua.replace(np.nan, '')
    df_esgoto = df_esgoto.replace(np.nan, '')
    return df_agua, df_esgoto
#--------------------------------------------------Script xX--------------------------------------------------
   
    