#MLB MODEL
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


#Player v Player

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


def getPlayerId(player_name):
    player_id = mlb.get_people_id(player_name)[0]
    return player_id

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


    pt = pd.DataFrame.from_dict(pitch_types)
    print(pt)
    cnt = pd.DataFrame.from_dict(counts)
    print(cnt)
    return pitch_types, counts


def create_buckets(count_batter, count_pitcher, pitch_types_batter):
    ### Working
    count_bucket = {}
    total = 0
    buckets = {} 
    count = 0
    for key,value in count_batter.items():
        total = total + count_batter[key]['result_in_count']
        count_bucket[key] = 0
        buckets[key] = 0
        buckets[key] = count_batter[key]['result_in_count']

    sum1 = 0
    for key,value in count_batter.items():
        count_bucket[key] = count_batter[key]['result_in_count']/total
        sum1 = sum1+ (count_batter[key]['result_in_count']/total)
        count = count + buckets[key]

        
    cb = pd.DataFrame.from_dict([count_bucket])
    #print(count)
    print(cb)
#print(balls)
#print(strikes)

####-------------------####
####-------------------####
#### --- MAIN AREA --- ####
####-------------------####
####-------------------####

pitcher_id = getPlayerId("Garrett Whitlock")
#print(pitcher_id)
batter_id = getPlayerId("Mike Trout")

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