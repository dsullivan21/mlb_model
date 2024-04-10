#TITLE: MLB MODEL
from time import perf_counter
from turtle import home
import statsapi
import json
from scipy import stats
from sklearn import datasets, svm
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import r2_score
from sklearn import preprocessing, svm
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import pandas as pd
import scipy

#player = statsapi.lookup_player('Devers, R')
#print(player[0]['id']) 

#stat = statsapi.player_stat_data(player[0]['id'], group="[hitting]", type="yearByYear", sportId=1)

#print(stat)
import mlbstatsapi
mlb = mlbstatsapi.Mlb()


##personIds = str(statsapi.lookup_player('Cole, G')[0]['id']) + ',' + str(statsapi.lookup_player('devers')[0]['id'])
#params = {'personIds':personIds, 'hydrate':'stats(group=[hitting,pitching],type=[statSplits],sitCodes=[vr,vl],season=2023)'}
#people = statsapi.get('people',params)

#for person in people['people']:
 #   print('{}'.format(person['fullName']))
#    for stat in person['stats']:
 #       if len(stat['splits']): print('  {}'.format(stat['group']['displayName']))
 #       for split in stat['splits']:
 #           print('    {} {}:'.format(split['season'], split['split']['description']))
 #           for split_stat,split_stat_value in split['stat'].items():
 #               print('      {}: {}'.format(split_stat, split_stat_value))
 #           print('\n')

#----------------------------------#
#----NOTE: GLOBAL VARIABLES -------#
#----------------------------------#

pitcher_throw_hand = ""
batter_hand = ""

all_batter_projs = {}


##------------------##
#Player v Player Stats
##------------------##
def player_v_player( pitcher_id, batter_id):
    #shohei_ohtani_id = mlb.get_people_id('Shohei Ohtani')[0]
    #ty_france_id = mlb.get_people_id('Ty France')[0]

    stats = ['vsPlayer']
    group = ['hitting']
    params = {'opposingPlayerId': pitcher_id, 'season': 2022}

    pvp_obj = {}

    stats = mlb.get_player_stats(batter_id, stats=stats, groups=group, **params)
    vs_player_total = stats['hitting']['vsplayertotal']
    for split in vs_player_total.splits:
        for k, v in split.stat.__dict__.items():
            pvp_obj[k] = 0
            pvp_obj[k] = v

           # 
    return pvp_obj
##---------------------------##
### Gets player Id from name ##
##---------------------------##
def getPlayerId(player_name):
    player_id = mlb.get_people_id(player_name)[0]
    return player_id

##---------------------------##
##  Get pitcher data needed  ##
##---------------------------##

def getPitcherData(pitcher_id, batter_id): 

    ##Get all pitches from starting pitcher in season 
   # nola = statsapi.lookup_player('nola,')[0]['id']
    hydrate = 'stats(group=[pitching],type=[pitchLog],season=2023,gameType=R)'
    r = statsapi.get('person',{'personId':pitcher_id, 'hydrate':hydrate})

    ## Get pitch arsenal
    hydrate = 'stats(group=[pitching],type=[pitchArsenal],season=2023,gameType=R)'
    ar = statsapi.get('person',{'personId':pitcher_id, 'hydrate':hydrate})

    pitches = ar['people'][0]['stats'][0]['splits']

    #save pitch arsenal
    arsenal = {}
    for p in pitches:
        pitch_type = p['stat']['type']['code']
        arsenal[pitch_type] = {}
        arsenal[pitch_type]['name'] = pitch_type
        arsenal[pitch_type]['percent'] = p['stat']['percentage']
        arsenal[pitch_type]['speed'] = p['stat']['averageSpeed']

    #print(arsenal)

    balls = {}
    strikes = {}
    #store count totals
    counts = {
        "0-0" : {},
        "0-1" : {},
        '0-2' : {},
        '1-0' : {},
        '1-1' : {},
        '1-2' : {},
        '2-0':  {},
        '2-1': {},
        '2-2': {},
        '3-0': {},
        '3-1': {},
        '3-2':  {}
    }

    if batter_id != None:
        batterVpitcher = {}

    #set up dicts with pitch arsenal
    for key, value in arsenal.items():
        balls[key] = {}
        strikes[key] = {}
        strikes[key]['count'] = 0
        strikes[key]['swinging'] = 0
        balls[key]['count'] = 0
        if batter_id != None:
            batterVpitcher[key] = {}
            batterVpitcher[key]['count'] = 0
        for key1, value1 in counts.items():
            counts[key1][key] = 0

    

    for d in r['people'][0]['stats'][0]['splits']:

        if "type" in d['stat']['play']['details']:

            if batter_id != None:
                if batter_id == d['batter']['id']:
                    print (d['stat']['play']['details'])
                    print("FOUND MATCHUP")
                    for key, value in batterVpitcher.items():
                        if d['stat']['play']['details']['type']['code'] == key:
                            batterVpitcher[key]['count'] += 1
                    


            #if strike
            if d['stat']['play']['details']['isStrike']==True:
                #find what pitch it was
                for key, value in strikes.items():
                    if d['stat']['play']['details']['type']['code'] == key:
                        strikes[key]['count'] += 1
                        if d['stat']['play']['details']['call']['code'] == "S" or d['stat']['play']['details']['call']['code'] == "W":
                            strikes[key]['swinging'] += 1
                        break

            #if ball
            if d['stat']['play']['details']['isBall']==True:
                #find what pitch it was
                for key, value in balls.items():
                    if d['stat']['play']['details']['type']['code']  == key:
                        balls[key]['count'] += 1
                        break
            
            #pitch freq per count
            if d['stat']['play']['count']['balls'] == 0 and d['stat']['play']['count']['strikes'] == 0:
                counts['0-0'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 1 and d['stat']['play']['count']['strikes'] == 0:
                counts['1-0'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 2 and d['stat']['play']['count']['strikes'] == 0:
                counts['2-0'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 3 and d['stat']['play']['count']['strikes'] == 0:
                counts['3-0'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 0 and d['stat']['play']['count']['strikes'] == 1:
                counts['0-1'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 0 and d['stat']['play']['count']['strikes'] == 2:
                counts['0-2'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 1 and d['stat']['play']['count']['strikes'] == 1:
                counts['1-1'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 1 and d['stat']['play']['count']['strikes'] == 2:
                counts['1-2'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 2 and d['stat']['play']['count']['strikes'] == 2:
                counts['2-2'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 2 and d['stat']['play']['count']['strikes'] == 1:
                counts['2-1'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 3 and d['stat']['play']['count']['strikes'] == 2:
                counts['3-2'][d['stat']['play']['details']['type']['code']] += 1
            elif d['stat']['play']['count']['balls'] == 3 and d['stat']['play']['count']['strikes'] == 1:
                counts['3-1'][d['stat']['play']['details']['type']['code']] += 1
            



    for key, value in counts.items():
        total = 0
        for key2, value2 in value.items():
            total = value2 + total
        counts[key]['total'] = total
    
    pt = pd.DataFrame.from_dict(counts)
    print(pt)
   # print(batterVpitcher)
    return counts, balls, strikes, batterVpitcher

##-------------------------------##
## Get Batter Game Log data -----##
##- Returns: object of L10 Data -##
##-------------------------------##
def getBatterRecentGames(batter_id):
    ## Get recent games stats ##
    #player_id = mlb.get_people_id(batter_name)[0]
    hydrate = 'stats(group=[hitting],type=[gameLog])'
    r = statsapi.get('person',{'personId':batter_id, 'hydrate':hydrate})
    r = r['people'][0]['stats'][0]['splits']

    #Init data storage
    last_ten_data = {}
    last_ten_data['atBats'] = 0
    last_ten_data['hits'] = 0
    last_ten_data['doubles'] = 0
    last_ten_data['home_runs'] = 0
    last_ten_data['triples'] = 0
    last_ten_data['totalBases'] = 0
    last_ten_data['strikeOuts'] = 0

    if len(r) <= 0:
        return None, None
    
   
    ##Dont overloop if theres more than 10 games played
    ## TODO: FIX THIS LATER

    if len(r) > 10:
        count = 0
        for game in r:
            
            if 'stat' in game:
                last_ten_data['atBats'] += game['stat']['atBats']
                last_ten_data['hits'] += game['stat']['hits']
                last_ten_data['doubles'] += game['stat']['doubles']
                last_ten_data['home_runs'] +=  game['stat']['homeRuns']
                last_ten_data['triples'] +=  game['stat']['triples']
                last_ten_data['totalBases'] += game['stat']['totalBases']
                last_ten_data['strikeOuts'] += game['stat']['strikeOuts']
    else:
        for game in r:
            if 'stat' in game:
                last_ten_data['atBats'] += game['stat']['atBats']
                last_ten_data['hits'] += game['stat']['hits']
                last_ten_data['doubles'] += game['stat']['doubles']
                last_ten_data['home_runs'] +=  game['stat']['homeRuns']
                last_ten_data['triples'] +=  game['stat']['triples']
                last_ten_data['totalBases'] += game['stat']['totalBases']
                last_ten_data['strikeOuts'] += game['stat']['strikeOuts']

    last_ten_data['outs'] = last_ten_data['atBats'] - last_ten_data['hits']
    last_ten_data['singles'] = last_ten_data['hits'] - (last_ten_data['doubles'] + last_ten_data['triples'] + last_ten_data['home_runs'])

    print(last_ten_data)

    return last_ten_data

##---------------------------##
##   Get batter data needed  ##
##---------------------------##
## RETURNS: Batter v Pitch type, Batter v Count, Batter ABs in Game, Batter w RISP ABs ##

def getBatterData(batter_id):

    #all player AB's in 2023
    hydrate = 'stats(group=[hitting],type=[pitchLog],season=2023,gameType=R)'
    r = statsapi.get('person',{'personId':batter_id, 'hydrate':hydrate})

    ## Store AB Results as game progresses ##
    ab_results = {}

    for i in range(1,5):
        ab_results[i] = {}
        ab_results[i]['hits'] = 0
        ab_results[i]['outs'] = 0
        ab_results[i]['singles'] = 0
        ab_results[i]['doubles'] = 0
        ab_results[i]['triples'] = 0
        ab_results[i]['home_runs'] = 0
        ab_results[i]['ba'] = 0

    ## RISP AB Results ##
    risp_ab = {}
    risp_ab['hits'] =0
    risp_ab['outs'] =0
    risp_ab['singles'] =0
    risp_ab['doubles'] =0
    risp_ab['triples'] =0
    risp_ab['home_runs'] =0
    risp_ab['ba'] =0

    ## Day/Night Storage Init##

    day_night_ABs = {}
    day_night_ABs['day'] = {}
    day_night_ABs['night'] = {}
    day_night_ABs['day']['hits'] = 0
    day_night_ABs['day']['outs'] = 0
    day_night_ABs['day']['singles'] = 0
    day_night_ABs['day']['doubles'] = 0
    day_night_ABs['day']['triples'] = 0
    day_night_ABs['day']['home_runs'] = 0
    day_night_ABs['day']['ba'] = 0
    day_night_ABs['night']['hits'] = 0
    day_night_ABs['night']['outs'] = 0
    day_night_ABs['night']['singles'] = 0
    day_night_ABs['night']['doubles'] = 0
    day_night_ABs['night']['triples'] = 0
    day_night_ABs['night']['home_runs'] = 0
    day_night_ABs['night']['ba'] = 0


    counts = {
        "0-0" : {},
        "0-1" : {},
        '0-2' : {},
        '1-0' : {},
        '1-1' : {},
        '1-2' : {},
        '2-0':  {},
        '2-1': {},
        '2-2': {},
        '3-0': {},
        '3-1': {},
        '3-2':  {}
    }

    for key, value in counts.items():

        counts[key]['result_in_count'] = 0
        counts[key]['count_freq'] = 0
        counts[key]['outs'] = 0
        counts[key]['walks'] = 0
        counts[key]['singles'] = 0
        counts[key]['doubles'] = 0
        counts[key]['triples'] = 0
        counts[key]['home_runs'] = 0

    pitch_types = {}

    #TODO: add lhp / rhp by pitch type? 
    

    #get data from AB's for pitch types
    #TODO: Refactor this, gotta be a better way 
    for d in r['people'][0]['stats'][0]['splits']:
        if "type" in d['stat']['play']['details']:
            if d['stat']['play']['details']['type']['code'] not in pitch_types:
                pitch_types[d['stat']['play']['details']['type']['code']] = {}
    
    #init pitch types counter
    for key, value in pitch_types.items():
        pitch_types[key]['count'] = 0
        pitch_types[key]['hits'] = 0
        pitch_types[key]['outs'] = 0
        pitch_types[key]['singles'] = 0
        pitch_types[key]['doubles'] = 0
        pitch_types[key]['triples'] = 0
        pitch_types[key]['home_runs'] = 0

    ab_count = 0
    prev_ab = 0
    for d in r['people'][0]['stats'][0]['splits']:
        
        if "type" in d['stat']['play']['details']:
            #print(d['stat']['play']['atBatNumber'])
           # print(prev_ab)
            if d['stat']['play']['atBatNumber'] > 0 and d['stat']['play']['atBatNumber'] >= prev_ab:
                if prev_ab != d['stat']['play']['atBatNumber'] and  d['stat']['play']['atBatNumber'] > prev_ab:
                    ab_count = ab_count + 1
                    prev_ab = d['stat']['play']['atBatNumber']
               # print(ab_count)
                if ab_count not in ab_results:
                    ab_results[ab_count] = {}
                    ab_results[ab_count]['hits'] = 0
                    ab_results[ab_count]['outs'] = 0
                    ab_results[ab_count]['singles'] = 0
                    ab_results[ab_count]['doubles'] = 0
                    ab_results[ab_count]['triples'] = 0
                    ab_results[ab_count]['home_runs'] = 0
                else:
                    if d['stat']['play']['details']['event'] == "single":
                        ab_results[ab_count]['hits'] +=1
                        ab_results[ab_count]['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        ab_results[ab_count]['hits'] +=1
                        ab_results[ab_count]['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        ab_results[ab_count]['hits'] +=1
                        ab_results[ab_count]['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        ab_results[ab_count]['hits'] +=1
                        ab_results[ab_count]['home_runs'] += 1
                    elif d['stat']['play']['details']['event'] == "strikeout":
                        ab_results[ab_count]['outs'] += 1
                    elif d['stat']['play']['details']['isInPlay'] == True:
                        ab_results[ab_count]['outs'] += 1
            else:
                ab_count = 0
                prev_ab =0
            temp = -1
            for key, value in pitch_types.items():
                if d['stat']['play']['details']['type']['code'] == key:
                    pitch_types[key]['count'] += 1
                    temp = key
                    break
            if d['stat']['play']['count']['runnerOn2b'] == True or d['stat']['play']['count']['runnerOn3b'] == True:
                if d['stat']['play']['details']['event'] == "single":
                    risp_ab['hits'] +=1
                    risp_ab['singles'] += 1
                elif d['stat']['play']['details']['event'] == "double":
                    risp_ab['hits'] +=1
                    risp_ab['doubles'] += 1
                elif d['stat']['play']['details']['event'] == "triple":
                    risp_ab['hits'] +=1
                    risp_ab['triples'] += 1
                elif d['stat']['play']['details']['event'] == "home_run":
                    risp_ab['hits'] +=1
                    risp_ab['home_runs'] += 1
                elif d['stat']['play']['details']['event'] == "strikeout":
                    risp_ab['outs'] +=1
                elif d['stat']['play']['details']['isInPlay'] == True:
                    risp_ab['outs'] +=1
            # Get results by pitch type
            if d['stat']['play']['details']['isInPlay'] == True:
                if d['stat']['play']['details']['event'] == "single":
                    pitch_types[temp]['singles'] += 1
                    pitch_types[temp]['hits'] += 1
                elif d['stat']['play']['details']['event'] == "double":
                    pitch_types[temp]['doubles'] += 1
                    pitch_types[temp]['hits'] += 1
                elif d['stat']['play']['details']['event'] == "triple":
                    pitch_types[temp]['triples'] += 1
                    pitch_types[temp]['hits'] += 1
                elif d['stat']['play']['details']['event'] == "home_run":
                    pitch_types[temp]['home_runs'] += 1
                    pitch_types[temp]['hits'] += 1
                else:
                    pitch_types[temp]['outs'] += 1
            elif d['stat']['play']['details']['event'] == "strikeout":
                pitch_types[temp]['outs'] += 1
            ## 0-0 count ##
            if d['stat']['play']['count']['balls'] == 0 and d['stat']['play']['count']['strikes'] == 0:
                counts['0-0']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['0-0']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['0-0']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['0-0']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['0-0']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['0-0']['home_runs'] += 1
                    else:
                        counts['0-0']['outs'] += 1
                        
             ## 1-0 count ##
            elif d['stat']['play']['count']['balls'] == 1 and d['stat']['play']['count']['strikes'] == 0:
                counts['1-0']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['1-0']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['1-0']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['1-0']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['1-0']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['1-0']['home_runs'] += 1
                    else:
                        counts['1-0']['outs'] += 1
            ## 2-0 count ##
            elif d['stat']['play']['count']['balls'] == 2 and d['stat']['play']['count']['strikes'] == 0:
                counts['2-0']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['2-0']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['2-0']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['2-0']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['2-0']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['2-0']['home_runs'] += 1
                    else:
                        counts['2-0']['outs'] += 1
            ## 3-0 count ##
            elif d['stat']['play']['count']['balls'] == 3 and d['stat']['play']['count']['strikes'] == 0:
                counts['3-0']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['3-0']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['3-0']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['3-0']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['3-0']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['3-0']['home_runs'] += 1
                    else:
                        counts['3-0']['outs'] += 1
                if d['stat']['play']['details']['event'] == "walk":
                    counts['3-0']['walks'] += 1
            ## 0-1 count ##
            elif d['stat']['play']['count']['balls'] == 0 and d['stat']['play']['count']['strikes'] == 1:
                counts['0-1']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['0-1']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['0-1']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['0-1']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['0-1']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['0-1']['home_runs'] += 1
                    else:
                        counts['0-1']['outs'] += 1
            ## 0 - 2 ##
            elif d['stat']['play']['count']['balls'] == 0 and d['stat']['play']['count']['strikes'] == 2:
                counts['0-2']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['0-2']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['0-2']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['0-2']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['0-2']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['0-2']['home_runs'] += 1
                    else:
                        counts['0-2']['outs'] += 1
                if d['stat']['play']['details']['event'] == 'strikeout':
                    counts['0-2']['outs'] += 1
            
            ## 1 - 1 ##
            elif d['stat']['play']['count']['balls'] == 1 and d['stat']['play']['count']['strikes'] == 1:
                counts['1-1']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['1-1']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['1-1']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['1-1']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['1-1']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['1-1']['home_runs'] += 1
                    else:
                        counts['1-1']['outs'] += 1
              #  if d['stat']['play']['details']['event'] == 'strikeout':
             #      counts['0-2']['outs'] += 1

             # 1 - 2 #
            elif d['stat']['play']['count']['balls'] == 1 and d['stat']['play']['count']['strikes'] == 2:
                counts['1-2']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['1-2']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['1-2']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['1-2']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['1-2']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['1-2']['home_runs'] += 1
                    else:
                        counts['1-2']['outs'] += 1
                if d['stat']['play']['details']['event'] == 'strikeout':
                    counts['1-2']['outs'] += 1
            ## 2 - 2 ##
            elif d['stat']['play']['count']['balls'] == 2 and d['stat']['play']['count']['strikes'] == 2:
                counts['2-2']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['2-2']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['2-2']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['2-2']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['2-2']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['2-2']['home_runs'] += 1
                    else:
                        counts['2-2']['outs'] += 1
                if d['stat']['play']['details']['event'] == 'strikeout':
                    counts['2-2']['outs'] += 1
            ## 2 - 1 ##
            elif d['stat']['play']['count']['balls'] == 2 and d['stat']['play']['count']['strikes'] == 1:
                counts['2-1']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['2-1']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['2-1']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['2-1']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['2-1']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['2-1']['home_runs'] += 1
                    else:
                        counts['2-1']['outs'] += 1
            ## 3 - 2 ##
            elif d['stat']['play']['count']['balls'] == 3 and d['stat']['play']['count']['strikes'] == 2:
                counts['3-2']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['3-2']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['3-2']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['3-2']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['3-2']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['3-2']['home_runs'] += 1
                    else:
                        counts['3-2']['outs'] += 1
                if d['stat']['play']['details']['event'] == 'strikeout':
                    counts['3-2']['outs'] += 1
                if d['stat']['play']['details']['event'] == "walk":
                    counts['3-2']['walks'] += 1
            ## 3 - 1 ##
            elif d['stat']['play']['count']['balls'] == 3 and d['stat']['play']['count']['strikes'] == 1:
                counts['3-1']['count_freq'] += 1
                if d['stat']['play']['details']['isInPlay'] == True:
                    counts['3-1']['result_in_count'] += 1
                    if d['stat']['play']['details']['event'] == "single":
                        counts['3-1']['singles'] += 1
                    elif d['stat']['play']['details']['event'] == "double":
                        counts['3-1']['doubles'] += 1
                    elif d['stat']['play']['details']['event'] == "triple":
                        counts['3-1']['triples'] += 1
                    elif d['stat']['play']['details']['event'] == "home_run":
                        counts['3-1']['home_runs'] += 1
                    else:
                        counts['3-1']['outs'] += 1
                if d['stat']['play']['details']['event'] == "walk":
                    counts['3-1']['walks'] += 1

    ##get batting avg on pitches
    for key, value in pitch_types.items():
        pitch_types[key]['ba'] = 0
        if (pitch_types[key]['hits'] + pitch_types[key]['outs']) != 0:
            pitch_types[key]['ba'] = pitch_types[key]['hits']/(pitch_types[key]['hits'] + pitch_types[key]['outs'])

    for key, value in counts.items():
        counts[key]['ba'] = 0
        hits = counts[key]['singles'] + counts[key]['doubles']+counts[key]['triples']+counts[key]['home_runs']
        if hits != 0:
            counts[key]['ba'] = hits/(hits+ counts[key]['outs'])

    ## Calc BA for AB's as game goes on ##
    for key, value in ab_results.items():
        if ab_results[key]['hits'] + ab_results[key]['outs'] != 0:
            ab_results[key]['ba'] = ab_results[key]['hits'] / (ab_results[key]['hits'] + ab_results[key]['outs'])
        else:
            ab_results[key]['ba'] = 0
    df = pd.DataFrame.from_dict(ab_results)
   # print(df)

    risp_ab['ba'] =  risp_ab['hits'] / (risp_ab['hits'] +risp_ab['outs'])
    #print(risp_ab)

    return pitch_types, counts, ab_results, risp_ab

##--------------------------------------------##
## start predictions from probability buckets ##
## Non ML Prediction, all stats based ##
## NOTE: Shooting out close to career averages for players v that pitcher 
##
## TODO: RISP odds for AB
## TODO: Bullpen v Batter
## TODO: Store strikeout chances for pitcher strikeout proj
##
##---------------------------------------------##

def create_buckets(count_batter, count_pitcher, pitch_types_batter, ab_results, pvp, l10_batter):
    ### Working
    count_bucket = {}
    total = 0
    buckets = {} 
    count = 0

    print(ab_results)
     ##Normalize buckets to make prediction 
    prev = 0
    ticker = 0
    for key,value in count_batter.items():
        total = total + count_batter[key]['result_in_count']
        count_bucket[key] = 0
        buckets[key] = 0
        buckets[key] = count_batter[key]['result_in_count']
        count_bucket[key] =  count_batter[key]['result_in_count']

    sum1 = 0
    for key,value in count_batter.items():
        count_bucket[key] = count_batter[key]['result_in_count']/total
        sum1 = sum1+ (count_batter[key]['result_in_count']/total)
        count = count + buckets[key]

    # DFs for testing visuals #
   # perc_bucket = pd.DataFrame.from_dict([count_bucket])
    # cb = pd.DataFrame.from_dict([buckets])


    #get % of pitch thrown in each count 
    pithcer_data = {}
    for key, val in count_pitcher.items():
        pithcer_data[key] = {}
        total = 0
        for key2, val2 in count_pitcher[key].items():
           # print(key2)
            if key2 != 'total':
                pithcer_data[key][key2] = 0
                total = count_pitcher[key]['total']
                pithcer_data[key][key2] = count_pitcher[key][key2]/count_pitcher[key]['total']



    pitcherData = pd.DataFrame.from_dict(pithcer_data)
    #print(pitcherData)

    hit_chance = 0
    ba_in_count = {}
    for key, val in pitch_types_batter.items():
        for key2, val2 in pithcer_data.items():
           # print (key2)
            if key2 not in ba_in_count:
                ba_in_count[key2] = 0
            for key3, val3 in pithcer_data[key2].items():
               # print(key2)
                if key3 == key:
            #        print( "BATTER: ", pitch_types_batter[key]['ba'])
            #        print("PITCHER: ", pithcer_data[key2][key])
                    ba_in_count[key2] = ba_in_count[key2]+ pitch_types_batter[key]['ba'] * pithcer_data[key2][key]
             #       print("COMBO: ", pitch_types_batter[key]['ba'] * pithcer_data[key2][key])
                

    # Total bases projection from straight data #
    total_bases =0
    for key, value in ba_in_count.items():
        hits_in_count = 0
        for key2,value2 in count_bucket.items():
            if key == key2:
                hit_chance = hit_chance + (count_bucket[key] * ba_in_count[key])
                #count_bucket[key]
              #  print(count_bucket[key] * ba_in_count[key])
                hits_in_count = count_batter[key]['singles'] + count_batter[key]['doubles'] +count_batter[key]['triples']+count_batter[key]['home_runs']
                if count_batter[key]['result_in_count'] != 0 and hits_in_count != 0:
                    single_chance = ((count_batter[key]['singles']/hits_in_count) * (count_bucket[key] * ba_in_count[key]))
                    double_chance = ((count_batter[key]['doubles']/hits_in_count) * (count_bucket[key] * ba_in_count[key]))*2
                    triple_chance = ((count_batter[key]['triples']/hits_in_count) * (count_bucket[key] * ba_in_count[key]))*3
                    hr_chance = ((count_batter[key]['home_runs']/hits_in_count) * (count_bucket[key] * ba_in_count[key]))*4
                    total_bases = total_bases + single_chance + double_chance +triple_chance+ hr_chance
                else: 
                     total_bases = total_bases + 0
                #print (count_bucket[key])

   # print (ba_count)

    ## -- AB's as Game Progressess -- ##

    ## - get a projection of ending count - ##

    ## - Model 4 ABs - ## 
    totalBasesProjected = 0
    ab_projected_data = {}
    ab_projected_data['singles'] = 0
    ab_projected_data['doubles'] = 0
    ab_projected_data['triples'] = 0
    ab_projected_data['home_runs'] = 0

    ## check if Player v Pitcher returned data
    ## get needed info from pvp
    pvp_arr = {}
    if pvp:
        outs = pvp['groundouts'] + pvp['airouts'] + pvp['strikeouts']
        doubles = pvp['doubles']
        singles = pvp['hits'] - (pvp['doubles'] + pvp['triples'] + pvp['homeruns'])
        homers = pvp['homeruns']
        triples = pvp['triples']
    
        pvp_arr['outs'] = outs
        pvp_arr['singles'] = singles
        pvp_arr['doubles'] = doubles
        pvp_arr['triples'] = triples
        pvp_arr['home_runs'] = homers

    
    for i in range (1,4):
        projected_count = getCountProjection(count_bucket)

        ## project on last 10 streak from batter ##
        l10_tb, l10_obj = projectResult(l10_batter)

        #First AB of Game Projection
        if i == 1:
            proj_by_ab, chance_by_ab = projectResult(ab_results[i])
            print(proj_by_ab, chance_by_ab)
        
        elif i == 2:
            proj_by_ab, chance_by_ab = projectResult(ab_results[i])
            print(proj_by_ab, chance_by_ab)
        elif i == 3:
            proj_by_ab, chance_by_ab = projectResult(ab_results[i])
            print(proj_by_ab, chance_by_ab)
        elif i == 4:
            proj_by_ab, chance_by_ab = projectResult(ab_results[i])
            print(proj_by_ab, chance_by_ab)

    ## - get projected result - #
        proj_tb_outcome, ab_proj_chances = projectResult(count_batter[projected_count])

        ## TODO: find a better way to project how many ABs v Starting Pitcher
        ## -----------------------------------------------
        ## TODO: Create AI to choose weights vs Manual 
        ## -----------------------------------------------

        if pvp_arr and l10_obj != None:
            pvp_tb, pvp_ab_proj = projectResult(pvp_arr)
            #print(pvp_tb, pvp_ab_proj)
            ab_projected_data['singles'] = ab_projected_data['singles'] + (ab_proj_chances['singles']*0.4 + chance_by_ab['singles']*0.2 + pvp_ab_proj['singles']*0.2 + l10_obj['singles']* 0.2)
            ab_projected_data['doubles'] = ab_projected_data['doubles'] + (ab_proj_chances['doubles']*0.4 + chance_by_ab['doubles']*0.2  + pvp_ab_proj['doubles']*0.2+ l10_obj['doubles']* 0.2)
            ab_projected_data['triples'] = ab_projected_data['triples'] + (ab_proj_chances['triples']*0.4 + chance_by_ab['triples']*0.2 + pvp_ab_proj['triples']*0.2+ l10_obj['triples']* 0.2)
            ab_projected_data['home_runs'] = ab_projected_data['home_runs'] + (ab_proj_chances['home_runs']*0.4 + chance_by_ab['home_runs']*0.2 + pvp_ab_proj['home_runs']*0.2 + l10_obj['home_runs']* 0.2)

            totalBasesProjected = totalBasesProjected + (proj_tb_outcome*0.4 + proj_by_ab * 0.2 + pvp_tb*0.2 +l10_tb*0.2)

            
        elif l10_obj != None:
            ab_projected_data['singles'] = ab_projected_data['singles'] + (ab_proj_chances['singles']*0.4 + chance_by_ab['singles']*0.3 + l10_obj['singles']* 0.3)
            ab_projected_data['doubles'] = ab_projected_data['doubles'] + (ab_proj_chances['doubles']*0.4 + chance_by_ab['doubles']*0.3 + l10_obj['doubles']* 0.3)
            ab_projected_data['triples'] = ab_projected_data['triples'] + (ab_proj_chances['triples']*0.4 + chance_by_ab['triples']*0.3 + l10_obj['triples']* 0.3)
            ab_projected_data['home_runs'] = ab_projected_data['home_runs'] + (ab_proj_chances['home_runs']*0.4 + chance_by_ab['home_runs']*0.3+ l10_obj['home_runs']* 0.3)

            totalBasesProjected = totalBasesProjected + (proj_tb_outcome*0.4 + proj_by_ab * 0.3+l10_tb*0.3)

        else:
            ab_projected_data['singles'] = ab_projected_data['singles'] + (ab_proj_chances['singles']*0.6 + chance_by_ab['singles']*0.4)
            ab_projected_data['doubles'] = ab_projected_data['doubles'] + (ab_proj_chances['doubles']*0.6 + chance_by_ab['doubles']*0.4 )
            ab_projected_data['triples'] = ab_projected_data['triples'] + (ab_proj_chances['triples']*0.6 + chance_by_ab['triples']*0.4 )
            ab_projected_data['home_runs'] = ab_projected_data['home_runs'] + (ab_proj_chances['home_runs']*0.6 + chance_by_ab['home_runs']*0.4)

            totalBasesProjected = totalBasesProjected + (proj_tb_outcome*0.6 + proj_by_ab * 0.4)

    print("Total Bases Proj: ", totalBasesProjected)
    print("Results Proj: ", ab_projected_data)

    
    print(count_batter[projected_count])

    return totalBasesProjected, ab_projected_data

    #print("HIT CHANCE: ", hit_chance)
    #print("TB's: ", total_bases)

    #count_p = pd.DataFrame.from_dict(count_batter)
    #print("Machado by Count: \n", count_p)
    #pitch_types_b = pd.DataFrame.from_dict(pitch_types_batter)
    #print("Machado by Pitch Type: \n", pitch_types_b)

    #count_pitch = pd.DataFrame.from_dict(count_pitcher)
    #print("Webb Pitch Type by count: \n", count_pitch)
   # print(pitch_types_b)
    #print(count)
   # print(cb)
#print(balls)
#print(strikes)


# -- Project an AB result -- #
# -- Returns AB Projection -- #
def projectResult(data):

    serizalied = []
    values = {}

   ## -- Make sample size larger for better projection
    for key, value in data.items():
        if key == "singles":
            for i in range(0,value*10):
                serizalied.append(1)
        elif key == "doubles":
            for i in range(0, value*10):
                serizalied.append(2)
        elif key == "triples":
            for i in range(0,value*10):
                serizalied.append(3)
        elif key == "home_runs":
            for i in range(0,value*10):
                serizalied.append(4)
        elif key == "outs":
            for i in range(0,value*10):
                serizalied.append(0)
    
    print(serizalied) 


    X = np.array(range(len(serizalied))).reshape(-1, 1)
    y = np.array(serizalied)

    if len(X) <= 0 or len(y) <=0:
        return None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)
    regressor = RandomForestRegressor()
    regressor.fit(X_train, y_train)
    predictions = regressor.predict(X_test)
    #clf = LinearRegression(n_jobs=-1)
    #clf.fit(X_train, y_train)
    #print( X_train, X_test, y_train, y_test)
    conf = regressor.score(X_test, y_test)

    print("confidence Score: ", conf)
    
    forecast_set = regressor.predict(X_test)
    print("projection: ", forecast_set)

    total = 0
    singles = 0
    doubles = 0
    triples = 0
    homeruns = 0
    outs = 0
    for x in forecast_set:
        if round(x) == 1:
            singles= singles+1
        elif round(x) == 2:
            doubles = doubles +1
        elif round(x) == 3:
            triples = triples +1
        elif round(x) == 4:
            homeruns = homeruns +1
        elif round(x) == 0:
            outs = outs + 1
        total = total +x

    ## -- aggregated projection of total bases
    total = total/len(forecast_set)

    ## -- AB projected chances data of occurances
    ab_perc_chances = {}

    homeruns = homeruns / len(forecast_set)
    singles = singles/len(forecast_set)
    doubles = doubles/len(forecast_set)
    triples = triples/len(forecast_set)
    outs = outs/len(forecast_set)

    ab_perc_chances['home_runs'] = homeruns
    ab_perc_chances['singles'] = singles
    ab_perc_chances['doubles'] = doubles
    ab_perc_chances['triples'] = triples
    ab_perc_chances['outs'] = outs


    print(total)
    print(ab_perc_chances)
   # print(data)

    return total, ab_perc_chances


## Serialize Data for Projecting ##
def getCountProjection(prob_array):
    print (prob_array)
    size_array = []
    value_array = {}
    serizalied = []

    count = 0
    for i in prob_array:
        value_array[i] = round(prob_array[i] * 1000)
        count = count+1
    
    #print(count)

    #    value_array[i].append(round(prob_array[i] * 1000))
        #value_array.append(i)
        #value_array[i].append(prob_array[i] * 500)
    
    #print(value_array)
    count = 0
    for key, value in value_array.items():
        for i in range(0, value):
            serizalied.append(count)
        count = count + 1
    

    X = np.array(range(len(serizalied))).reshape(-1, 1)
    y = np.array(serizalied)

    if len(X) <= 0 or len(y) <=0:
        return None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)
    regressor = RandomForestRegressor()
    regressor.fit(X_train, y_train)
    predictions = regressor.predict(X_test)
    #clf = LinearRegression(n_jobs=-1)
    #clf.fit(X_train, y_train)
    #print( X_train, X_test, y_train, y_test)
    conf = regressor.score(X_test, y_test)

    print("confidence Score: ", conf)
    
    forecast_set = regressor.predict(X_test)
    print("projection: ", forecast_set)

    total = 0
    #print(type(forecast_set))
    for x in forecast_set:
        total = total + x

    ## Off of prediction matrix, get average for the count projection
    ## Total stores count projection 
    total = round(total / len(forecast_set))
    countToUse = ''
    if total == 0:
        countToUse = "0-0"
    elif total == 1:
        countToUse = "0-1"
    elif total == 2:
        countToUse = "0-2"
    elif total == 3:
        countToUse = "1-0"
    elif total == 4:
        countToUse = "1-1"
    elif total == 5:
        countToUse = "1-2"
    elif total == 6:
        countToUse = "2-0"
    elif total == 7:
        countToUse = "2-1"
    elif total == 8:
        countToUse = "2-2"
    elif total == 9:
        countToUse = "3-0"
    elif total == 10:
        countToUse = "3-1"
    elif total == 11:
        countToUse = "3-2"

    print(countToUse)
    print(total)
    print (serizalied)

    return countToUse
    #for i in range (0,1000):
    #    size_array[]


####-------------------####
####-------------------####
#### --- MAIN AREA --- ####
####-------------------####
####-------------------####

def main():


    with open('lineup.json') as json_file:
        lineups = json.load(json_file)

    pitcher_id = getPlayerId("Patrick Corbin")
    print(lineups)
    for player in lineups:
        
        all_batter_projs[player] = {}
        all_batter_projs[player]['total_bases'] = 0
        all_batter_projs[player]['singles'] = 0
        all_batter_projs[player]['doubles'] = 0
        all_batter_projs[player]['triples'] = 0
        all_batter_projs[player]['home_runs'] = 0

        
        #print(pitcher_id)
        batter_id = getPlayerId(player)

        l_10_batter = getBatterRecentGames(batter_id)


        count_pitcher, balls, strikes, batterVpitcher = getPitcherData(pitcher_id, batter_id)
        pitch_types, count_batter,ab_results, risp_results = getBatterData(batter_id)

        pvp = player_v_player(pitcher_id, batter_id)


#serializeProbabilities(count_batter)

        tb, res = create_buckets(count_batter, count_pitcher, pitch_types, ab_results, pvp, l_10_batter)

        print(tb)
        all_batter_projs[player]['singles'] = res['singles'] 
        all_batter_projs[player]['doubles'] = res['doubles']
        all_batter_projs[player]['triples'] = res['triples']
        all_batter_projs[player]['home_runs'] = res['home_runs']
        all_batter_projs[player]['total_bases'] = tb

        
main()
df = pd.DataFrame.from_dict(all_batter_projs)
print(df)



#print(r)


#https://statsapi.mlb.com/api/v1/people/605151?hydrate=stats(group=[hitting,pitching,fielding],type=[gameLog])


#pitcher_id = getPlayerId("James Paxton")
#batter_id = getPlayerId("Byron Buxton")
#player_v_player(pitcher_id, batter_id)


#with open('nola.json', 'w', encoding='utf-8') as f:
 #   json.dump(r['people'][0]['stats'][0]['splits'], f, ensure_ascii=False, indent=4)


## GET SCHEDULE ##

#schedule = mlb.get_schedule("4/6/2024")
#dates = schedule.dates
#players = []
#for date in dates:
#    for game in date.games:
#        box = mlb.get_game_box_score(game_id=game.gamepk)
#        players = box.teams.home.players
#        break

#for p in players:
#    print(players[p].PlayersDictPerson)


#def getPitchData(player_name): 
#    player_id = mlb.get_people_id(player_name)[0]
#    stats = ['pitchLog']
#    group = ['pitching']
#    params = {'season': 2023}
#    stats = mlb.get_player_stats(player_id, stats=stats, groups=group, **params)
#    career_pitching_stat = stats['pitching']['season']
#    for split in career_pitching_stat.splits:
#        for k, v in split.stat.__dict__.items():
#            print(k, v)
#    stats = ['pitchLog']
#    group = ['pitching']
#    params = {'season': 2023}
    # let's get some stats
#    stats = mlb.get_player_stats(player_id, stats=stats, groups=group, **params)
#    print(stats['pitching']['pitchArsenal'])
    #print(career_pitching_stat)


#getPitchData('Shohei Ohtani')