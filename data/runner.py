from __future__ import absolute_import
from __future__ import print_function

import datetime
import pytz

import os
import traci
import sumolib
import sys
import optparse
import traci.constants as tc
import traci
import random
import string

import traci.exceptions

import pandas as pd

def getdatetime():
        utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        currentDT = utc_now.astimezone(pytz.timezone("Europe/Paris"))
        DATIME = currentDT.strftime("%Y-%m-%d %H:%M:%S")
        return DATIME

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    # tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    # sys.path.append(tools)
    SUMO_HOME = os.environ['SUMO_HOME']
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


# Fonction pour obtenir une position d'arrêt sécurisée
def get_safe_stop_position(current_position, min_distance, lane_length):
    # Calculer la position minimale sécurisée
    safe_stop_position = current_position + min_distance
    # Vérifier si la position calculée dépasse la longueur de la voie
    if safe_stop_position >= lane_length:
        safe_stop_position = lane_length - 1  # Assurez-vous que la position ne dépasse pas la longueur de la voie
    return safe_stop_position

def generate_random_stop_position(current_position, lane_length, min_distance, max_distance):
    # max_possible_position = min(current_position + max_distance, lane_length)
    # return random.uniform(current_position + min_distance, max_possible_position)
    # Assurez-vous que la position actuelle + min_distance est valide
    min_possible_position = current_position + min_distance
    if min_possible_position >= lane_length:
        min_possible_position = lane_length - 1  # Assurez-vous que la position ne dépasse pas la longueur de la voie
    
    # Calculez la position maximale possible
    max_possible_position = min(current_position + max_distance, lane_length - 1)
    
    # Générer une position d'arrêt aléatoire dans les limites valides
    return random.uniform(min_possible_position, max_possible_position)

def get_max_speed(lane_id):
    return traci.lane.getMaxSpeed(lane_id)

def get_traffic_density(edge_id):
    lane_count = traci.edge.getLaneNumber(edge_id)
    lane_ids = [f"{edge_id}_{i}" for i in range(lane_count)]
    total_vehicles = sum([traci.lane.getLastStepVehicleNumber(lane_id) for lane_id in lane_ids])
    # total_length = sum([traci.lane.getLength(lane_id) for lane_id in lane_ids])
    # if total_length > 0:
    #     return total_vehicles / total_length
    return total_vehicles

# def get_nearby_traffic_lights(vehicle_id):
#     vehicle_position = traci.vehicle.getPosition(vehicle_id)
#     traffic_lights = traci.trafficlight.getIDList()
#     for tl_id in traffic_lights:
#         tl_position = traci.trafficlight.getPosition(tl_id)
#         distance = sumolib.geomhelper.distance(vehicle_position, tl_position)
#         if distance <= 100:
#             return tl_id, distance
#     return None, None

def get_nearby_vehicle(veh_id, proximity_distance):
    """
    Retourne les véhicules à proximité d'un véhicule donné,
    classés comme étant devant ou derrière le véhicule cible, et ayant le même itinéraire.

    Args:
    - vehicle_id (str): L'ID du véhicule cible.
    - proximity_distance (float): La distance maximale pour qu'un véhicule soit considéré comme à proximité.

    Returns:
    - tuple: (vehicules_devant, vehicules_derriere)
      vehicules_devant et vehicules_derriere sont des listes contenant les IDs des véhicules correspondants.
    """
    # Récupérer la liste de tous les véhicules dans la simulation
    vehicle_ids = traci.vehicle.getIDList()
    
    # Obtenir la position et l'itinéraire du véhicule cible
    x_target, y_target = traci.vehicle.getPosition(veh_id)
    route_target = traci.vehicle.getRoute(veh_id)
    
    vehicles_ahead = []
    vehicles_behind = []

    # Parcourir tous les véhicules pour vérifier leur proximité et leur position par rapport au véhicule cible
    for v_id in vehicle_ids:
        if v_id != veh_id:
            # Vérifier si le véhicule a le même itinéraire
            if traci.vehicle.getRoute(v_id) == route_target:
                # Obtenir la position du véhicule actuel
                x, y = traci.vehicle.getPosition(v_id)
                
                # Calculer la distance entre le véhicule cible et le véhicule actuel
                distance = traci.simulation.getDistance2D(x_target, y_target, x, y, isDriving=True)
                
                # Vérifier si cette distance est inférieure ou égale à la distance de proximité
                if distance <= proximity_distance:
                    # Comparer les positions longitudinales
                    # Comparer les positions longitudinales
                    lane_pos_target = traci.vehicle.getLanePosition(veh_id)
                    lane_pos_current = traci.vehicle.getLanePosition(v_id)
                    
                    if lane_pos_current > lane_pos_target:
                        vehicles_ahead.append(v_id)
                    else:
                        vehicles_behind.append(v_id)
    
    return vehicles_ahead, vehicles_behind


def execute_random_action(vehicle_id):
    """
    Execute une action aleatoire (acceleration, deceleration, stop) sur un vehicule.

    Args:
    - vehicle_id (str): L'ID du véhicule cible.

    Returns:
    - dict: Les caracteristiques de l'action executée.
    """
    
    action_id = 1
    # action_id = random.randint(1, 3)
    duration = random.randint(5, 20)
    print("====================================== ACtion =======================================")

    current_edge = traci.vehicle.getRoadID(vehicle_id)
    current_lane = traci.vehicle.getLaneID(vehicle_id)
    # road_type = get_road_type(current_edge)
    max_speed = get_max_speed(current_lane)
    traffic_density = get_traffic_density(current_edge)
    # tl_id, tl_distance = get_nearby_traffic_lights(vehicle_id)
    
    
    action = {
        "id": action_id,
        "max_speed": max_speed,
        "veh_neighbors": traffic_density,
        "tls": traci.vehicle.getNextTLS(vehicle_id),
        "param": 0,
        "duration": duration,
        "allowed_speed" : traci.vehicle.getAllowedSpeed(vehicle_id)
    }
    
    if action_id == 1:
        param = random.uniform(3, 10)
        current_speed= traci.vehicle.getSpeed(vehicle_id)
        # traci.vehicle.setMaxSpeed(vehicle_id, 25)
        traci.vehicle.setAcceleration(vehicle_id, param, duration)
        # traci.vehicle.setSpeed(vehicle_id, max(current_speed+3, max_speed))
        action["action"] = "accelerate"
        action["param"] = param
    
    elif action_id == 2:
        param = random.uniform(2, 15)
        # param = 1
        traci.vehicle.slowDown(vehicle_id, param, duration)
        action["action"] = "decelerate"
        action["param"] = param
    
    elif action_id == 3:
        # stop_duration = 20  # Stop duration in seconds
        traci.vehicle.setSpeed(vehicle_id, 0.0)  # Set vehicle speed to 0
        
        print(traci.simulation.getDeltaT())
        for step in range(int(duration / traci.simulation.getDeltaT()) + 1):
            # print("**********Dans Action***************")
            traci.simulationStep()
        traci.vehicle.setSpeed(vehicle_id, -1)  # Resume normal behavior
        action["action"] = "stop"
    
    return action




def is_vehicle_in_sim(vehicle_id):
    """
        Verifie si un vehicule est encore dans la simulation

        Args:
        - vehicle_id: l'ID du vehicule

        Returns:
        - Bool
    """
    actual_vehicle = traci.vehicle.getIDList()
    if vehicle_id in actual_vehicle:
        return True
    else: return False

def set_max_speed_on_route(vehicle_id):
    route = traci.vehicle.getRoute(vehicle_id)
    for edge_id in route:
        lane_count = traci.edge.getLaneNumber(edge_id)
        lane_ids = [f"{edge_id}_{i}" for i in range(lane_count)]
        for lane_id in lane_ids:
            actual_max_speed = traci.lane.getMaxSpeed(lane_id)
            traci.lane.setMaxSpeed(lane_id, actual_max_speed+15)

def set_max_speed_on_all_edges(factor=2):
    edges = traci.edge.getIDList()
    for edge_id in edges:
        lane_count = traci.edge.getLaneNumber(edge_id)
        lane_ids = [f"{edge_id}_{i}" for i in range(lane_count)]
        for lane_id in lane_ids:
            actual_max_speed = traci.lane.getMaxSpeed(lane_id)
            traci.lane.setMaxSpeed(lane_id, actual_max_speed * factor)

def set_vehicle_max_speed_by_wc(veh_id, condition):
    """
        Definit une vitesse maximale en fonction des conditions meteorologiques

        Args:
        - vehicle_id (str): L'ID du véhicule cible.
        - condition (str): la condition meteorologique

        Returns:
        - None.
    """
    factor = 1
    if condition == "clear":
        pass
    elif condition == "rain":
        factor= 0.8
    elif condition == "snow":
        factor= 0.6
    elif condition == "fog":
        factor= 0.7
    elif condition == "storm":
        factor= 0.5

    traci.vehicle.setMaxSpeed(veh_id, 15 * factor)
             

def apply_weather_conditions(condition):
    """
        Change les caracteristiques de la simulation en fonction des conditions meteorologiques

        Args:
        - condition (str): la condition meteorologique

        Returns:
        - None.
    """
    
    if condition == "clear":
        # Reset to normal conditions
        print("####   CLEAR   ########")
        set_max_speed_on_all_edges(factor=1)
    elif condition == "rain":
        print("###### RAIN ##########")
        traci.simulation.setParameter("", "friction", "0.7")
        set_max_speed_on_all_edges(factor=0.8)
    elif condition == "snow":
        print("######## SNOW ########")
        traci.simulation.setParameter("", "friction", "0.5")
        set_max_speed_on_all_edges(factor=0.6)
    elif condition == "fog":
        print("############ FOG #############")
        traci.simulation.setParameter("", "friction", "0.8")
        set_max_speed_on_all_edges(factor=0.7)
    elif condition == "storm":
        print("############# STORM ##################3")
        traci.simulation.setParameter("", "friction", "0.4") 
        set_max_speed_on_all_edges(factor=0.5)
    # Add more conditions as needed



# def random_string(length=6):
#     letters = string.ascii_lowercase
#     return ''.join(random.choice(letters) for i in range(length))

# def generate_random_entry_times(num_vehicles, start_step, end_step):
#     return sorted(random.randint(start_step, end_step) for _ in range(num_vehicles))

# Fonction pour ajouter des véhicules aléatoires autour de veh1
def add_random_vehicles(num_vehicles):

    """
    Permet d'ajouter un nombre precis de vehicule à la simulation avec la meme trajectoire que le veh veh1.

    Args:
    - num_vehicles (int): Nombre de vehicules à ajouter.

    Returns:
    - tuple (veh_devant, veh_derriere): Respectivement nombre de vehicules ajouté avant et apres le vehicule veh1.
    """
    
    # Id des edges constituant la trajectoire de veh1
    veh1_route = ['18605558#0', '18605558#3', '221966545#1', '221966545#3', '221966545#4', '221966545#5', '221966546', '18604777#0', 
                  '18604834#0', '18604834#2', '18604849', '26285638#0', '26285638#1', '18604414', '84816934#0', '-93612858#4', '-93612858#3', 
                  '-93612858#1', '-93612858#0', '-93612860#1', '-18604401#4', '-18604401#3', '18604226#1']
    
    # veh1_speed = traci.vehicle.getSpeed(veh_id)
    veh1_type = "veh_passenger"
    # veh1_lane = traci.vehicle.getLaneID(veh_id)
    veh_ahead, veh_behind = 0, 0

    for i in range(num_vehicles):
        entry_time = random.randint(5, 15)
        new_vehicle_id = f"randomVeh_{i}"
        # Ajoute le véhicule sur la même route
        traci.vehicle.add(new_vehicle_id, "", depart=entry_time, typeID=veh1_type)
        traci.vehicle.setRoute(new_vehicle_id, list(veh1_route))
        traci.vehicle.setColor(new_vehicle_id, (0, 0, 255, 255))
        if entry_time <= 10:
            veh_ahead += 1
        else: veh_behind += 1

    return veh_ahead, veh_behind


def get_vehicles_ahead(vehicle_id, distance_threshold=200):
    """
    Retourne le nombre de véhicules devant vehicle_id dans un rayon donné ainsi que leurs IDs.
    """
    vehicles_ahead = []
    vehicle_position = traci.vehicle.getPosition(vehicle_id)
    vehicle_lane = traci.vehicle.getLaneID(vehicle_id)

    all_vehicles = traci.vehicle.getIDList()

    for veh in all_vehicles:
        if veh != vehicle_id:
            veh_position = traci.vehicle.getPosition(veh)
            veh_lane = traci.vehicle.getLaneID(veh)

            # Vérifier si le véhicule est sur la même voie
            if veh_lane == vehicle_lane:
                distance = veh_position[0] - vehicle_position[0]
                # Vérifier si le véhicule est devant et dans le rayon spécifié
                if distance > 0 and distance < distance_threshold:
                    vehicles_ahead.append(veh)

    return vehicles_ahead

def run(with_action:bool):

    try:
        
        traci.start(sumoCmd)
    

        travel_time = 0
        fuel_consumtion = 0
        co2_emission = 0
        action = {"id":0, 
                  "action": "Aucune", 
                  "param":0, 
                  "duration":0, 
                  "max_speed": 0,
                  "veh_neighbors" : 0, 
                  "tls" : None,
                  "param": 0,
                  "allowed_speed" : 0}
        # action = []
        action_position = None
        simulation_data = None
        x, y, lon, lat, speed, acceleration = 0, 0, 0, 0, 0, 0
        veh_leader = 0
        veh_flw = 0
        veh_nbr = 0
        veh_ahead = []
        veh_behind = []
        left_leaders = 0
        right_leaders = 0

        # Générer un moment aléatoire pour exécuter l'action
        random_time = random.randint(11, 70)  # Par exemple, entre 50 et 500 secondes
        # random_time = 60
        print("random time", random_time)

        set_max_speed_on_all_edges()
        # nbr_veh_to_add = random.randint(0,15)
        nbr_veh_to_add = 0

        veh_ahead_added,veh_behind_added = add_random_vehicles(nbr_veh_to_add)


        # ID du vehicule que nous voulons suivre
        vehicle_id = "veh1"

        # Vitesse maximale sur toutes les voies de la simulation
        

        # Attendre que le véhicule entre dans la simulation
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            if is_vehicle_in_sim(vehicle_id):
                print(f"Vehicle {vehicle_id} inserted into the simulation.")
                break
        
        
        traci.vehicle.setMaxSpeed(vehicle_id, 30)
        traci.vehicle.setColor(vehicle_id, (255, 0, 0))

        # add_surrounding_vehicles(vehicle_id, 5)
       

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            if is_vehicle_in_sim(vehicle_id):

                # speed mode = [0,1,1,1,1,0]
                traci.vehicle.setSpeedMode(vehicle_id, 30)
            

                if with_action:
                    # Exécuter une action aléatoire lorsque le temps de simulation atteint le moment aléatoire
                    if traci.simulation.getTime() == random_time:
                        acceleration = traci.vehicle.getAcceleration(vehicle_id)
                        speed = traci.vehicle.getSpeed(vehicle_id)
                        veh_ahead, veh_behind = get_nearby_vehicle(vehicle_id, 100)
                        x, y = traci.vehicle.getPosition(vehicle_id)
                        lon, lat = traci.simulation.convertGeo(x, y)
                        action = execute_random_action(vehicle_id) 
                        # Récupérer la position du véhicule lorsque l'action est exécutée ainsi que la vitesse avant l'action
                        
                        


                fuel_consumtion += traci.vehicle.getFuelConsumption(vehicle_id) * traci.simulation.getDeltaT()
                co2_emission += traci.vehicle.getCO2Emission(vehicle_id) * traci.simulation.getDeltaT()
                # print("###################################################################################")
                # print("Vitesse du vehicule:", traci.vehicle.getSpeed(vehicle_id))
                # print("Vitesse du vehicule Sans Traci:", traci.vehicle.getSpeedWithoutTraCI(vehicle_id))
                # print("Acceleration du vehicule:", traci.vehicle.getAcceleration(vehicle_id))
                # print("###################################################################################")
                

                travel_time = traci.simulation.getTime() - traci.vehicle.getDeparture(vehicle_id)
                

                simulation_data = [random_time, vehicle_id, x, y , lon, lat, speed, acceleration, fuel_consumtion, co2_emission, travel_time,
                                   action["id"], action["action"], action["param"], action["duration"], action["max_speed"], action["veh_neighbors"],
                                   action["allowed_speed"], nbr_veh_to_add, veh_ahead_added, veh_behind_added, len(veh_ahead), len(veh_behind)]
                    

                
            else: 
                print("Vehicule sortie de la simulation")
                break
        # print(f"Veh1 route ID: {list(traci.vehicle.getRoute(vehicle_id))}")
        return simulation_data

            
    
    except traci.exceptions.TraCIException:
        print("Une connexion traci est deja active")
        return None
    
    except KeyboardInterrupt:
        traci.close()
        sys.stdout.flush()

    finally:
        traci.close()





if __name__ == '__main__':
    # Chemin vers le répertoire contenant les fichiers de configuration
    SUMO_CONFIG_FILE = os.path.join("C:", os.sep, "Users", "USER", "Sumo", "2024-05-03-15-56-56", "osm.sumocfg")
    sumoBinary = sumolib.checkBinary('sumo')
    sumoCmd = [sumoBinary, "-c", SUMO_CONFIG_FILE,
               "--tripinfo-output", "tripinfo.xml",
               "--device.emissions.probability", "1",
               "--collision.action", "warn",
               "--collision.stoptime", "10"]

    # datas = pd.DataFrame(columns=["DateTime", "VehicleID", "X", "Y", "Longitude", "Latitude", "Speed(m/s)", "FuelConsumption(mg)", "CO2Emission(mg)", "TravelTime(s)", "ActionId", "ActionName", "ActionParam"])
    datas = pd.DataFrame(columns=["DateTime", "VehicleID", "X", "Y", "Longitude", "Latitude", "Speed", "Acceleration", "FuelConsumption", "CO2Emission", "TravelTime", "ActionId", "ActionName", "ActionParam", "ActionDuration", 
                                  "LaneMaxSpeed", "Neighbors", "AllowedSpeed", "VehicleAdded", "VehicleAddedAhead", "VehicleAddedBehind", "ActionVehicleAhead", "ActionVehicleBehind"])

    
    for i in range(100):
        print(f"Simulation n0: {i+1}")
        data= run(False)
        datas.loc[len(datas)] = data

    datas.to_csv("reference_without_add2.csv", index=False)

    # data = run(True)
    # print("data", data)
    # datas.to_csv("data.csv", index=False)