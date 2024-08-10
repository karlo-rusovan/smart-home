import tkinter as tk
import spade
from temperature_sensor import TemperatureSensorAgent
from motion_sensor import MotionSensorAgent
from motion_controller import MotionControllerAgent
from temperature_controller import TemperatureControllerAgent
from gas_sensor import GasSensorAgent
from electricity_sensor import ElectricitySensorAgent
from resource_controller import ResourceControllerAgent
from indoor_light_sensor import InLightSensorAgent
from outside_light_sensor import OutLightSensorAgent
from light_controller import LightControllerAgent
from lights_actuator import LightsActuatorAgent
from blinds_actuator import BlindsActuatorAgent
from radiator_actuator import RadiatorActuatorAgent
from heater_actuator import HeaterActuatorAgent
from AC_actuator import ACActuatorAgent
import tkinter as tk
import threading
import sys
import asyncio
import re

class MultiStdoutRedirector:
    def __init__(self, textboxes_filters):
        self.textboxes_filters = textboxes_filters

    def write(self, message):
        lines = message.split('\n')
        for line in lines:
            if line.strip():
                for textbox, filter_keyword in self.textboxes_filters:
                    if filter_keyword in line:
                        line = re.sub(r'^.*?:', '', line).strip()
                        textbox.insert(tk.END, line + '\n')
                        textbox.see(tk.END)
    def flush(self):
        pass

class SharedState:
    def __init__(self):
        self.temperature = None
        self.motion = None
        self.gas = None
        self.electricity = None
        self.initialize = None
        self.outdoor_light = None
        self.indoor_light = None
        self.desired_light = None
        self.desired_temp = None

    def set_temperature(self, temperature):
        self.temperature = temperature

    def get_temperature(self):
        return self.temperature

    def set_motion(self, motion):
        self.motion = motion

    def get_motion(self):
        return self.motion

    def set_gas(self, gas):
        self.gas = gas

    def get_gas(self):
        return self.gas

    def set_electricity(self, electricity):
        self.electricity = electricity

    def get_electricity(self):
        return self.electricity

    def set_initialize(self, initialize):
        self.initialize = initialize

    def get_initialize(self):
        return self.initialize
    
    def set_outdoor_light(self, outdoor_light):
        self.outdoor_light = outdoor_light

    def get_outdoor_light(self):
        return self.outdoor_light
    
    def set_indoor_light(self, indoor_light):
        self.indoor_light = indoor_light

    def get_indoor_light(self):
        return self.indoor_light
    
    def set_desired_light(self, desired_light):
        self.desired_light = desired_light
    
    def get_desired_light(self):
        return self.desired_light

    def set_desired_temp(self, desired_temp):
        self.desired_temp = desired_temp

    def get_desired_temp(self):
        return self.desired_temp

class App:
    def __init__(self, root, state):
        self.state = state
        self.root = root
        self.root.title("Agent Control Panel")
        self.root.geometry("1920x1080")

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_frame = tk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=10)

        self.temp_label = tk.Label(self.top_frame, text="Temperature:", padx=10, pady=5)
        self.temp_label.grid(row=0, column=0, sticky=tk.W)
        self.temp_entry = tk.Entry(self.top_frame, width=30)
        self.temp_entry.insert(0, "20")
        self.temp_entry.grid(row=0, column=1, pady=5)

        self.motion_label = tk.Label(self.top_frame, text="Motion (occupied/empty):", padx=10, pady=5)
        self.motion_label.grid(row=0, column=2, sticky=tk.W)
        self.motion_entry = tk.Entry(self.top_frame, width=30)
        self.motion_entry.grid(row=0, column=3, pady=5)

        self.gas_label = tk.Label(self.top_frame, text="Gas (good/low):", padx=10, pady=5)
        self.gas_label.grid(row=1, column=0, sticky=tk.W)
        self.gas_entry = tk.Entry(self.top_frame, width=30)
        self.gas_entry.insert(0, "good")
        self.gas_entry.grid(row=1, column=1, pady=5)

        self.electricity_label = tk.Label(self.top_frame, text="Electricity (good/low):", padx=10, pady=5)
        self.electricity_label.grid(row=1, column=2, sticky=tk.W)
        self.electricity_entry = tk.Entry(self.top_frame, width=30)
        self.electricity_entry.insert(0, "good")
        self.electricity_entry.grid(row=1, column=3, pady=5)
        
        self.outdoor_light_label = tk.Label(self.top_frame, text="Outdoor light level (lumens/m2):", padx=10, pady=5)
        self.outdoor_light_label.grid(row=2, column=0, sticky=tk.W)
        self.outdoor_light_entry = tk.Entry(self.top_frame, width=30)
        self.outdoor_light_entry.insert(0, "6000")
        self.outdoor_light_entry.grid(row=2, column=1, pady=5)

        self.indoor_light_label = tk.Label(self.top_frame, text="Indoor light level (lumens/m2):", padx=10, pady=5)
        self.indoor_light_label.grid(row=2, column=2, sticky=tk.W)
        self.indoor_light_entry = tk.Entry(self.top_frame, width=30)
        self.indoor_light_entry.insert(0, "200")
        self.indoor_light_entry.grid(row=2, column=3, pady=5)

        self.desired_temp_label = tk.Label(self.top_frame, text="Desired temperature:", padx=10, pady=5)
        self.desired_temp_label.grid(row=3, column=0, sticky=tk.W)
        self.desired_temp_entry = tk.Entry(self.top_frame, width=30)
        self.desired_temp_entry.insert(0, "22")
        self.desired_temp_entry.grid(row=3, column=1, pady=5)

        self.desired_light_label = tk.Label(self.top_frame, text="Desired light level (lumens):", padx=10, pady=5)
        self.desired_light_label.grid(row=3, column=2, sticky=tk.W)
        self.desired_light_entry = tk.Entry(self.top_frame, width=30)
        self.desired_light_entry.insert(0, "300")
        self.desired_light_entry.grid(row=3, column=3, pady=5)

        self.initialize_label = tk.Label(self.top_frame, text="Initialize agents?", padx=10, pady=5)
        self.initialize_label.grid(row=4, column=0, sticky=tk.W)
        self.initialize_entry = tk.Entry(self.top_frame, width=30)
        self.initialize_entry.grid(row=4, column=1, pady=5)

        self.log_frame = tk.Frame(self.main_frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_label1 = tk.Label(self.log_frame, text="ResourceController Log")
        self.log_label1.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.log_textbox1 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox1.grid(row=1, column=0, pady=5, padx=(0, 20))

        self.log_label2 = tk.Label(self.log_frame, text="MotionController Log")
        self.log_label2.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.log_textbox2 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox2.grid(row=3, column=0, pady=5, padx=(0, 20))

        self.log_label3 = tk.Label(self.log_frame, text="TemperatureController Log")
        self.log_label3.grid(row=4, column=0, sticky=tk.W, pady=5)
        self.log_textbox3 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox3.grid(row=5, column=0, pady=5, padx=(0, 20))

        self.log_label4 = tk.Label(self.log_frame, text="LightController Log")
        self.log_label4.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.log_textbox4 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox4.grid(row=1, column=1, pady=5, padx=(0, 20))

        self.log_label5 = tk.Label(self.log_frame, text="LightsActuator Log")
        self.log_label5.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.log_textbox5 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox5.grid(row=3, column=1, pady=5, padx=(0, 20))

        self.log_label6 = tk.Label(self.log_frame, text="BlindsActuator Log")
        self.log_label6.grid(row=4, column=1, sticky=tk.W, pady=5)
        self.log_textbox6 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox6.grid(row=5, column=1, pady=5, padx=(0, 20))

        self.log_label7 = tk.Label(self.log_frame, text="RadiatorActuator Log")
        self.log_label7.grid(row=0, column=2, sticky=tk.W, pady=5)
        self.log_textbox7 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox7.grid(row=1, column=2, pady=5, padx=(0, 20))

        self.log_label8 = tk.Label(self.log_frame, text="HeaterActuator Log")
        self.log_label8.grid(row=2, column=2, sticky=tk.W, pady=5)
        self.log_textbox8 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox8.grid(row=3, column=2, pady=5, padx=(0, 20))

        self.log_label9 = tk.Label(self.log_frame, text="ACActuator Log")
        self.log_label9.grid(row=4, column=2, sticky=tk.W, pady=5)
        self.log_textbox9 = tk.Text(self.log_frame, wrap='word', height=15, width=70)
        self.log_textbox9.grid(row=5, column=2, pady=5, padx=(0, 20))

        self.update_gui()
        
        self.filters = [
            (self.log_textbox1, "ResourceController"),
            (self.log_textbox2, "MotionController"),
            (self.log_textbox3, "TemperatureController"),
            (self.log_textbox4, "LightController"),
            (self.log_textbox5, "LightsActuator"),
            (self.log_textbox6, "BlindsActuator"),
            (self.log_textbox7, "RadiatorActuator"),
            (self.log_textbox8, "HeaterActuator"),
            (self.log_textbox9, "ACActuator")
        ]

        self.stdout_redirector = MultiStdoutRedirector(self.filters)
        sys.stdout = self.stdout_redirector

    def update_gui(self):
        self.set_temperature()
        self.set_motion()
        self.set_gas()
        self.set_electricity()
        self.set_initialize()
        self.set_outdoor_light()
        self.set_indoor_light()
        self.set_desired_light()
        self.set_desired_temp()
        self.root.after(3000, self.update_gui)

    def set_temperature(self):
        temp = self.temp_entry.get()
        self.state.set_temperature(temp)

    def set_motion(self):
        motion = self.motion_entry.get()
        self.state.set_motion(motion)

    def set_gas(self):
        gas = self.gas_entry.get()
        self.state.set_gas(gas)

    def set_electricity(self):
        electricity = self.electricity_entry.get()
        self.state.set_electricity(electricity)

    def set_initialize(self):
        initialize = self.initialize_entry.get()
        self.state.set_initialize(initialize)

    def set_outdoor_light(self):
        outdoor_light = self.outdoor_light_entry.get()
        self.state.set_outdoor_light(outdoor_light)

    def set_indoor_light(self):
        indoor_light = self.indoor_light_entry.get()
        self.state.set_indoor_light(indoor_light)

    def set_desired_temp(self):
        desired_temp = self.desired_temp_entry.get()
        self.state.set_desired_temp(desired_temp)

    def set_desired_light(self):
        desired_light = self.desired_light_entry.get()
        self.state.set_desired_light(desired_light)    

def run_gui(state):
    try:
        root = tk.Tk()        
        app = App(root, state)
        root.mainloop()
    except Exception as e:
        print(f"Exception in GUI thread: {e}")

async def main():
    state = SharedState()    
    with open('agent_addresses.txt', 'w') as file:
        pass
    gui_thread = threading.Thread(target=run_gui, args=(state,))
    gui_thread.start() 
    while state.get_initialize() != "yes":
        await asyncio.sleep(3)    

    temperatureController = TemperatureControllerAgent('tempcontroller@desktop-ms7hl0s', "password")
    temperatureSensor = TemperatureSensorAgent('tempsensor@desktop-ms7hl0s', "password")
    motionSensor = MotionSensorAgent('motionsensor@desktop-ms7hl0s', "password")
    motionController = MotionControllerAgent('motioncontroller@desktop-ms7hl0s', "password")
    electricitySensor = ElectricitySensorAgent('electricitysensor@desktop-ms7hl0s', "password")
    gasSensor = GasSensorAgent('gassensor@desktop-ms7hl0s', "password")
    resourceController = ResourceControllerAgent('resourcecontroller@desktop-ms7hl0s', "password")
    outLightSensor = OutLightSensorAgent('outlightsensor@desktop-ms7hl0s', "password")
    inLightSensor = InLightSensorAgent('inlightsensor@desktop-ms7hl0s', "password")
    lightController = LightControllerAgent('lightcontroller@desktop-ms7hl0s', "password")
    lightsActuator = LightsActuatorAgent('lightsactuator@desktop-ms7hl0s', "password")
    blindsActuator = BlindsActuatorAgent('blindsactuator@desktop-ms7hl0s', "password")
    radiatorActuator = RadiatorActuatorAgent('radiatoractuator@desktop-ms7hl0s', "password")
    heaterActuator = HeaterActuatorAgent('heateractuator@desktop-ms7hl0s', "password")
    acActuator = ACActuatorAgent('acactuator@desktop-ms7hl0s', "password")

    temperatureSensor.state = state
    motionSensor.state = state
    gasSensor.state = state
    electricitySensor.state = state
    inLightSensor.state = state
    outLightSensor.state = state
    temperatureController.state = state
    lightController.state = state

    await temperatureController.start()
    await resourceController.start()
    await motionController.start()
    await gasSensor.start()
    await electricitySensor.start()
    await motionSensor.start()    
    await temperatureSensor.start()   
    await outLightSensor.start()
    await inLightSensor.start()
    await lightsActuator.start()
    await blindsActuator.start()
    await lightController.start()
    await radiatorActuator.start()
    await heaterActuator.start()
    await acActuator.start()


    await spade.wait_until_finished(temperatureController)
    await resourceController.stop()
    await motionController.stop()
    await gasSensor.stop()
    await electricitySensor.stop()
    await motionSensor.stop() 
    await outLightSensor.stop()
    await inLightSensor.stop()
    await lightController.stop()
    await lightsActuator.stop()
    await blindsActuator.stop()
    await radiatorActuator.stop()
    await heaterActuator.stop()
    await acActuator.stop()
    print('Gotovo')

if __name__ == "__main__":
    spade.run(main())