from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from helper_functions import publish_state_change

class TemperatureSensorAgent(Agent):
    class TemperatureSensorBehaviour(PeriodicBehaviour):
        def __init__(self,period,state):
            super().__init__(period)
            self.state = state

        async def on_start(self):
            with open('agent_addresses.txt', 'a') as f:
                f.write(f";{self.agent.jid}\n")
            
        async def run(self):
            heat =  self.state.get_temperature() 
            await publish_state_change('tempSensor', 'heat', 'sensors', str(heat), self)
        
        async def on_end(self):
            await self.agent.stop()
        
    async def setup(self):
        state = self.state
        behaviour = self.TemperatureSensorBehaviour(period=10, state=state)
        self.add_behaviour(behaviour)