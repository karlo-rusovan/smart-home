from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from helper_functions import publish_state_change

class GasSensorAgent(Agent):
    class GasSensorBehaviour(PeriodicBehaviour):
        def __init__(self,period,state):
            super().__init__(period)
            self.state = state

        async def on_start(self):      
            with open('agent_addresses.txt', 'a') as f:
                f.write(f";{self.agent.jid}\n")
            
        async def run(self):
            gas =  self.state.get_gas()                   
            await publish_state_change('gasSensor', 'gas', 'sensors', str(gas), self)
        
        async def on_end(self):    
            await self.agent.stop()
        
    async def setup(self):
        state = self.state
        behaviour = self.GasSensorBehaviour(period=10, state=state)
        self.add_behaviour(behaviour)