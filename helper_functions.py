from spade.message import Message

async def publish_state_change (subscription, type, ontology, body, self):
    with open('agent_addresses.txt', 'r') as f:
        lines = f.readlines()            
        for line in lines:
            agent_subscriptions, agent_jid = line.strip().split(';')
            agent_subscriptions = agent_subscriptions.strip().split(',')
            for agent_subscription in agent_subscriptions:  
                if agent_subscription == subscription:          
                    notify_msg = Message(
                        to=agent_jid,
                        body=body,
                        metadata={
                            "type": type,
                            "ontology": ontology,
                            "language": "english",
                            "performative": "inform",
                        }
                    )
                    await self.send(notify_msg)