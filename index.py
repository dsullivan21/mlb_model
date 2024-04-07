#MLB MODEL
from time import perf_counter
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



##------------------##
#Player v Player Stats
##------------------##
def player_v_player( pitcher_id, batter_id):
    #shohei_ohtani_id = mlb.get_people_id('Shohei Ohtani')[0]
    #ty_france_id = mlb.get_people_id('Ty France')[0]

    stats = ['vsPlayer']
    group = ['hitting']
    params = {'opposingPlayerId': pitcher_id, 'season': 2022}

    stats = mlb.get_player_stats(batter_id, stats=stats, groups=group, **params)
    vs_player_total = stats['hitting']['vsplayertotal']
    for split in vs_player_total.splits:
        for k, v in split.stat.__dict__.items():
            print(k, v)
           # print (vs_player_total)

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

##---------------------------##
##   Get batter data needed  ##
##---------------------------##
def getBatterData(batter_id):

    #all player AB's in 2023
    hydrate = 'stats(group=[hitting],type=[pitchLog],season=2023,gameType=R)'
    r = statsapi.get('person',{'personId':batter_id, 'hydrate':hydrate})

    
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

    
    for d in r['people'][0]['stats'][0]['splits']:
        if "type" in d['stat']['play']['details']:
            temp = -1
            for key, value in pitch_types.items():
                if d['stat']['play']['details']['type']['code'] == key:
                    pitch_types[key]['count'] += 1
                    temp = key
                    break
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

    return pitch_types, counts

##--------------------------------------------##
## start predictions from probability buckets ##
## Non ML Prediction, all stats based ##
## NOTE: Shooting out close to career averages for players v that pitcher 
##---------------------------------------------##

def create_buckets(count_batter, count_pitcher, pitch_types_batter):
    ### Working
    count_bucket = {}
    total = 0
    buckets = {} 
    count = 0
     ##Normalize buckets to make prediction 
    prev = 0
    ticker = 0
    for key,value in count_batter.items():
        total = total + count_batter[key]['result_in_count']
        count_bucket[key] = 0
        buckets[key] = 0
      #  if ticker == 0:
        buckets[key] = count_batter[key]['result_in_count']
       # else:
       #     buckets[key] = count_batter[key]['result_in_count'] + prev
      #  prev = buckets[key]
     #   ticker = ticker + 1
        count_bucket[key] =  count_batter[key]['result_in_count']

    sum1 = 0
    for key,value in count_batter.items():
        count_bucket[key] = count_batter[key]['result_in_count']/total
        sum1 = sum1+ (count_batter[key]['result_in_count']/total)
        count = count + buckets[key]

    perc_bucket = pd.DataFrame.from_dict([count_bucket])
    cb = pd.DataFrame.from_dict([buckets])

    print(perc_bucket)

    #mu, std = scipy.stats.norm.fit(cb)

    # generate data for var_2
   # var_2 = np.random.normal(mu, std, size=len(cb))

   # print (var_2)

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
                    

    #print(ba_in_count)

    #ba_count = pd.DataFrame.from_dict(ba_in_count)

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
    print("HIT CHANCE: ", hit_chance)
    print("TB's: ", total_bases)

    count_p = pd.DataFrame.from_dict(count_batter)
    print("Machado by Count: \n", count_p)
    pitch_types_b = pd.DataFrame.from_dict(pitch_types_batter)
    print("Machado by Pitch Type: \n", pitch_types_b)

    count_pitch = pd.DataFrame.from_dict(count_pitcher)
    print("Webb Pitch Type by count: \n", count_pitch)
   # print(pitch_types_b)
    #print(count)
   # print(cb)
#print(balls)
#print(strikes)

####-------------------####
####-------------------####
#### --- MAIN AREA --- ####
####-------------------####
####-------------------####

pitcher_id = getPlayerId("Logan Webb")
#print(pitcher_id)
batter_id = getPlayerId("Manny Machado")

count_pitcher, balls, strikes, batterVpitcher = getPitcherData(pitcher_id, batter_id)
pitch_types, count_batter = getBatterData(batter_id)

create_buckets(count_batter, count_pitcher, pitch_types)


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