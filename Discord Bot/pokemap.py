#requires a pygeoj data set
import datetime
import pygeoj
import pickle

#This adds a pokestop to the map at coordinates = [latitude, longitude] with a given name
#  this does not check for duplicate names yet, so should be used with care
#  still need to come up with a system for handling duplicates 
def add_stop(taskmap,coordinates,name):
    taskmap.add_feature(properties={'marker-size': 'medium', 'marker-symbol': '', 'marker-color': '#808080', 'Stop Name': name, 'Task': '', 'Reward': '',
                                    'Last Edit': int(datetime.datetime.now().strftime("%j")), 'nicknames': []
                                   },
                        geometry={"type":"Point", "coordinates":coordinates, "bbox": [coordinates[0], coordinates[1], coordinates[0], coordinates[1]]} )

def reset_old_tasks(taskmap):
#    backup_name = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_task_backup.json'
#    taskmap.save(backup_name)
    for stop in taskmap:
        if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
            reset_task(stop)
    
def reset_task(stop):
    stop.properties['Task'] = ''
    stop.properties['Reward'] = ''
    stop.properties['marker-color'] = '#808080'
    stop.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))
    
def reset_all_tasks(taskmap):
    backup_name = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_task_backup.json'
    taskmap.save(backup_name)
    for stop in taskmap:
        reset_task(stop)
        
def find_stop(taskmap,stop_name):       
    stop_not_found = True
    while stop_not_found:
        for stop in taskmap:
            if stop.properties['Stop Name'] == stop_name:
                if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
                    reset_all_tasks(stop)
                return stop
                stop_not_found = False
        break
    if stop_not_found:
        raise ValueError('Stop name not found')

def set_task(stop,task):
    if stop.properties['Task'] == '':
        stop.properties['Task'] = task.quest
        stop.properties['Reward'] = task.reward
        stop.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))
        if task.reward_type == 'Encounter':
            if task.shiny:
                stop.properties['marker-color'] = '#ffff00'
            else:
                stop.properties['marker-color'] = '#008000'
        elif task.reward_type == 'Stardust':
            stop.properties['marker-color'] = '#ff00ff'
        elif task.reward_type == 'Item':
            stop.properties['marker-color'] = '#0000ff'
        elif task.reward_type == 'Rare Candy':
            stop.properties['marker-color'] = '#ff8000'
    else:
        raise ValueError('Task Already Set')
        
        
class Task:
    def __init__(self, reward, quest, reward_type, shiny):
        self.reward = reward
        self.quest = quest
        self.reward_type = reward_type
        self.shiny = shiny

def find_task(tasklist,task_str):
    #doesn't handle tasks with the same reward well
    task_not_found = True
    while task_not_found:
        for tasks in tasklist:
            if (task_str == tasks.reward) or (task_str == tasks.quest):
                return tasks
                task_not_found = False
    if stop_not_found:
        raise ValueError('Task not found')
        
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)