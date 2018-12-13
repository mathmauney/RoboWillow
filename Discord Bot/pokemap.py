#requires a pygeoj data set
import datetime
import pygeoj
import pickle

#This adds a pokestop to the map at coordinates = [latitude, longitude] with a given name
#  this does not check for duplicate names yet, so should be used with care
#  still need to come up with a system for handling duplicates 
def add_stop(taskmap,coordinates,name):
    taskmap.add_feature(properties={'marker-size': 'medium', 'marker-symbol': '', 'marker-color': '#808080', 'Stop Name': name, 'Task': '', 'Reward': '',
                                    'Last Edit': int(datetime.datetime.now().strftime("%j")), 'Nicknames': []
                                   },
                        geometry={"type":"Point", "coordinates":coordinates, "bbox": [coordinates[0], coordinates[1], coordinates[0], coordinates[1]]} )

def reset_old_tasks(taskmap):
    stops_reset = False
#    backup_name = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_task_backup.json'
#    taskmap.save(backup_name)
    for stop in taskmap:
        if stop.properties.get('Last Edit',0) != int(datetime.datetime.now().strftime("%j")):
            reset_task(stop)
            stops_reset = True
    return stops_reset
    
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
    stops_found = []
    for stop in taskmap:
        if (stop.properties['Stop Name'].title() == stop_name.title() or stop.properties['Stop Name'].title() == stop_name.title()) :
            if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
                reset_all_tasks(taskmap)
            stops_found.append(stop)
    if len(stops_found) == 0:
        raise ValueError('Stop name not found')
    elif len(stops_found) == 1: 
        return stops_found[0]
    else:
        temp_num = 1;
        for stop in stops_found:
            if not(stop.properties['Nicknames']):
                stop.properties['Nicknames'].append('temp' + str(temp_num))
                temp_num += 1
        raise MutlipleStopsFound(stops_found)

def set_task(stop,task):
    if stop.properties['Task'] == '':
        stop.properties['Task'] = task.quest
        stop.properties['Reward'] = task.reward
        stop.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))
        stop.properties['Category'] = task.reward_type
    else:
        raise TaskAlreadyAssigned(stop,task)
        
        


def find_task(tasklist,task_str):
    #doesn't handle tasks with the same reward well
    task_str = task_str.title()
    task_not_found = True
    while task_not_found:
        for tasks in tasklist:
            if (task_str == tasks.reward.title()) or (task_str == tasks.quest.title()):
                return tasks
                task_not_found = False
        break
    if task_not_found:
        raise ValueError('Task not found')
        
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
        
def add_stop_nickname(stop,nickname):
    if 'Nicknames' not in stop.properties:
        stop.properties['Nicknames'] = []
    if (len(stop.properties['Nicknames']) == 1 and stop.properties['Nicknames'][0].startswith('temp')):
        stop.properties['Nicknames'][0] = nickname
    else:
        stop.properties['Nicknames'].append(nickname)
    
def add_task_nickname(task,nickname):
    task.nicknames.append(nickname)
    
###Classes
#Task Class
class Task():
    def __init__(self, reward, quest, reward_type, shiny):
        self.reward = reward
        self.quest = quest
        self.reward_type = reward_type
        self.shiny = shiny
        self.nicknames = [];
        
###Custom Exceptions
"""Base class for the module so all module exceptions can be caught together"""
class PokemapException(Exception):
    def __init__(self):
        self.message = 'No error message set, contact maintainer'

class TaskAlreadyAssigned(PokemapException):
    """Exception for trying to assign a new task to a stop that already has one"""
    def __init__(self, stop = None, task = None):
        if (stop is None):
            msg = "Failed to assign task as stop"
        elif (task is None):
            msg = "Failed to assign task to " + stop.properties['Stop Name'] + " as it already had task " + stop.properties['Task']
        else:
            msg = "Failed to assign " + task.reward + " to " + stop.properties['Stop Name'] + " as it already had task " + stop.properties['Task']
        self.message = msg
        
class MutlipleStopsFound(PokemapException):
    """Exception for when multiple stops are found using the same stop search query"""
    def __init__(self, stops = None):
        msg = "Multiple stops found with this name. Use stop nicknames to prevent this. Stops without nicknames have been given temporary nicknames, please add unique nicknames now."
        if not(stops is None):
            msg += ' Nicknames for these stops include: '
            for stop in stops:
                msg += stop.properties['Nicknames'][0] + ', '
            msg = msg [:-2] + '.'    
        self.message = msg
