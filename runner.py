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


def execute_random_action(vehicle_id):
    # Générer une action aléatoire (0 pour accélérer, 1 pour décélérer, 2 pour s'arrêter)
    action_id = random.randint(0, 2)
    # action_id = 2
    duration = random.randint(5, 20)  # Durée d'arrêt aléatoire entre 5 et 20 secondes
    # print("=============================================================================")
    
    if action_id == 0:
        param = random.uniform(3, 10)
        # print("Vitesse avant :", traci.vehicle.getSpeed(vehicle_id))
        traci.vehicle.setAcceleration(vehicle_id, param, duration)
        # print("Vitesse apres :", traci.vehicle.getSpeed(vehicle_id))
        return {"id"    : 0,
                "action" : "accelerate",
                "param": param,
                "duration" : duration}
    
    elif action_id == 1:
        param = random.uniform(2, 10)
        # print("Vitesse avant :", traci.vehicle.getSpeed(vehicle_id))
        traci.vehicle.slowDown(vehicle_id, param, duration)
        # print("Vitesse apres :", traci.vehicle.getSpeed(vehicle_id))
        return {"id"    : 1,
                "action" : "decelerate",
                "param": param,
                "duration": duration}
    else:
        # duration = random.randint(5, 20)  # Durée d'arrêt aléatoire entre 5 et 20 secondes
        # print("Vitesse avant :", traci.vehicle.getSpeed(vehicle_id))
        current_position = traci.vehicle.getLanePosition(vehicle_id)
        # Obtenez l'ID de la voie actuelle du véhicule
        lane_id = traci.vehicle.getLaneID(vehicle_id)
        # Obtenez la longueur de la voie
        lane_length = traci.lane.getLength(lane_id)
        stop_position = get_safe_stop_position(current_position, 75, lane_length)


        # stop_position = generate_random_stop_position(traci.vehicle.getLanePosition(vehicle_id), lane_length, 50, 200)
        traci.vehicle.setStop(vehicle_id, 
                              edgeID=traci.vehicle.getRoadID(vehicle_id),
                              pos= stop_position, 
                              duration=duration)
        # print("Vitesse apres :", traci.vehicle.getSpeed(vehicle_id))
        return {"id"    : 2,
                "action" : "stop",
                "param" : 0,
                "duration": duration}



def is_vehicle_in_sim(vehicle_id):
    actual_vehicle = traci.vehicle.getIDList()
    if vehicle_id in actual_vehicle:
        return True
    else: return False
             

def run(with_action:bool):

    try:
        
        traci.start(sumoCmd)
    

        travel_time = 0
        fuel_consumtion = 0
        co2_emission = 0
        action = {"id":None, "action": None, "param":0, "duration":0}
        # action = []
        action_position = None
        simulation_data = None
        x, y, lon, lat, speed = 0, 0, 0, 0, 0

        # Générer un moment aléatoire pour exécuter l'action
        random_time = random.randint(1, 80)  # Par exemple, entre 50 et 500 secondes
        print("random time", random_time)

        # action_id = random.randint(0, 2)
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            # ID du vehicule que nous voulons suivre
            vehicle_id = "veh1"
            

            if is_vehicle_in_sim(vehicle_id):

                # speed mode = [0,1,1,0,0,0]
                traci.vehicle.setSpeedMode(vehicle_id, 24)
                # traci.vehicle.setSpeed(vehicle_id, 10)

                if with_action:
                    # Exécuter une action aléatoire lorsque le temps de simulation atteint le moment aléatoire
                    
                    # nb_of_actions = 2
                    if traci.simulation.getTime() == random_time:
                        action = execute_random_action(vehicle_id) 
                        # Récupérer la position du véhicule lorsque l'action est exécutée ainsi que la vitesse avant l'action
                        x, y = traci.vehicle.getPosition(vehicle_id)
                        lon, lat = traci.simulation.convertGeo(x, y)
                        speed = traci.vehicle.getSpeed(vehicle_id)

                    # if traci.simulation.getTime() == 25:
                        # action.append( execute_random_action(vehicle_id, action_id) )
                        # # Récupérer la position du véhicule lorsque l'action est exécutée ainsi que la vitesse avant l'action
                        # x, y = traci.vehicle.getPosition(vehicle_id)
                        # lon, lat = traci.simulation.convertGeo(x, y)
                        # speed = traci.vehicle.getSpeed(vehicle_id)

                fuel_consumtion += traci.vehicle.getFuelConsumption(vehicle_id) * traci.simulation.getDeltaT()
                co2_emission += traci.vehicle.getCO2Emission(vehicle_id) * traci.simulation.getDeltaT()
                # print("###################################################################################")
                # print("Vitesse du vehicule:", traci.vehicle.getSpeed(vehicle_id))
                # print("Vitesse du vehicule Sans Traci:", traci.vehicle.getSpeedWithoutTraCI(vehicle_id))
                # print("Acceleration du vehicule:", traci.vehicle.getAcceleration(vehicle_id))
                # print("###################################################################################")

                # #  Vérifier si le véhicule a atteint sa destination
                # if traci.vehicle.getRoadID(vehicle_id) == traci.vehicle.getRoute(vehicle_id)[-1]:
                travel_time = traci.simulation.getTime() - traci.vehicle.getDeparture(vehicle_id)
                #     # print("Consommation:", fuel_consumtion)
                #     # print("Émissions de CO2:", co2_emission)
                #     print("Temps de trajet:", travel_time)
                #     # print("Action", action["action"])
                #     # metrics["travel_time"] = traci.vehicle.getAccumulatedWaitingTime(vehicle_id)

                simulation_data = [random_time, vehicle_id, x, y , lon, lat, speed, fuel_consumtion, co2_emission, travel_time, action["id"], action["action"], action["param"], action["duration"]]
                    

                # # Afficher les métriques
                #     # print(simulation_data, simulation_data)
                # print("Consommation:", fuel_consumtion)
                # print("Émissions de CO2:", co2_emission)
                # print("Temps de trajet:", travel_time)
                # print("action", action["id"])
                #     # print("Action exécutée:", action)
                #     # print("Position lors de l'action:", [x, y])
                #     # print("Position GPS", [lon, lat])
                #     # print("Waiting time", traci.vehicle.getAccumulatedWaitingTime(vehicle_id))
                #     break  # Sortir de la boucle une fois que les métriques sont collectées
                    

                # if vehicle_id is not None:
                #     # Récupérer la position du véhicule
                #     vehicle_position = traci.vehicle.getPosition(vehicle_id)

                #     # Récupérer la vitesse du véhicule
                #     vehicle_speed = traci.vehicle.getSpeed(vehicle_id)

                #     # Afficher les données récupérées
                #     print("ID du véhicule:", vehicle_id)
                #     print("Position du véhicule:", vehicle_position)
                #     print("Vitesse du véhicule:", vehicle_speed)
                #     print("Emission CO2", traci.vehicle.getCO2Emission(vehicle_id))
                #     print("Consommation Essence", traci.vehicle.getFuelConsumption(vehicle_id))
            else: break
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
               "--device.emissions.probability", "1"]

    # datas = pd.DataFrame(columns=["DateTime", "VehicleID", "X", "Y", "Longitude", "Latitude", "Speed(m/s)", "FuelConsumption(mg)", "CO2Emission(mg)", "TravelTime(s)", "ActionId", "ActionName", "ActionParam"])
    datas = pd.DataFrame(columns=["DateTime", "VehicleID", "X", "Y", "Longitude", "Latitude", "Speed", "FuelConsumption", "CO2Emission", "TravelTime", "ActionId", "ActionName", "ActionParam", "ActionDuration"])


    for i in range(400):
        data= None
        if i==0:
            data= run(False)
        else:
            data = run(True)
        datas.loc[len(datas)] = data

    datas.to_csv("final_data4.csv", index=False)

    # data = run(True)
    # print("data", data)

    # for i in range(100):
    #     simulation_data = run()
    #     datas.loc[len(datas)] = simulation_data

    # datas.to_csv("data.csv", index=False)