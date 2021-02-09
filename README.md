# Simple_Maps-6.009_Project
 Shows you the shortest and the fastest path to a given destination from a starting point. All the relevant code is in lab.py.
 Unfortunately, the entirety of the Cambridge map was too big to be uploaded to github. 
 
 ## Visualizing the Code
You can start the server by running server.py but providing the filename of one of the datasets as an argument, for example:

python3 server.py midwest
or 
python server.py midwest

(If you are not using a terminal to run your code, you can replace sys.argv[1] in server.py with a hard-coded name of a dataset, like 'midwest', which you can then change later to load in different datasets.)

This process will first build up the necessary auxiliary structures for pathfinding by calling your build_auxiliary_structures function, and then it will start a server. After the server has successfully started, you can interact with this application by navigating to http://localhost:6009/ in your web browser. In that view, you can double-click on two locations to find and display a path between them.

Alternatively, you can manually call your path-finding procedure to generate a path and then pass its path to the provided to_local_kml_url function to receive a URL that will initialize to display the resulting path. For example, to show a path from Adam H's high school to Timber Edge Alpaca Farms (where he worked in high school), you could run the following:

phs = (41.375288, -89.459541)
timber_edge = (41.452802, -89.443683)
aux = build_auxiliary_structures('resources/midwest.nodes', 'resources/midwest.ways')
print(to_local_kml_url(find_short_path(aux, phs, timber_edge)))
which should print out a URL that, when pasted into the browser, shows the path you found (assuming the server is running). If you started the server with the midwest dataset loaded, you can then double-click around that area to find other paths.


## Fastest Path 
If, after starting server.py, you open the following URL in your browser (note the difference from above), the web UI will use your find_fast_path instead of find_short_path for pathfinding when double-clicking:

http://localhost:6009/?type=fast
 
