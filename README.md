# RoboWillow

RoboWillow is a discord bot designed principly to facilitate the reporting and mapping of Pokemon Go research tasks. This is currently very much a work in process and shouldn't be deployed for anything other than testing. The rest of this README is still a template at this point, and will be updated as the project gets more finalized. 


### Prerequisites
Python3 (and pip) (Python 3.7 has issues with discord.py currently)

Web Hosting

### Installing
Download the source code and move it to appropriate locations. The html page and img folder should go to whereever the map is to be hosted, and the Bot folder can be moved whereever is convenient

run: 'pip install -r requirements.txt' to install dependencies. 

## Getting Started
To run the bot a discord token is needed, which is specified in config.py. To run the map a MapBox token is needed, and should be specified in token.js. Other config options are at the start of robo_willow.py and should be edited to fit your community, and the map data location should be changed in index.html. (These will hopefully be moved to better locations in later versions)

Once the configs have been set for your commmunity, the bot can be run using 'python3 robo_willow.py' and can be invited to your server using the discord developer portal where you got the discord token.

Once the bot has been added correctly, use the setup command to get walked through setting the map up, and the help command to see how to operate the bot.

## Current Features

### Research Map

A leaflet map based on the bot's geoJSON data can be found [here](https://mathmauney.github.io/RoboWillow/). Tasks for a stop can be viewed by clicking on a stop if a task has been reported. The map also supports filtering the tasks by reward and has custom icons for some tasks.

### Discord Bot

The discord bot supports task reporting and mapping. Tasks are currently reset at midnight server time, though this will be fixed in later versions. The help (and help advanced) commands can be used to see all the 


### About Project

## Authors

* **Alex Mauney** - *Initial work* - [MathMauney](https://github.com/mathmauney)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

All software is licensed under MIT license.

Icons are from The Artifical under a CC-BY license
