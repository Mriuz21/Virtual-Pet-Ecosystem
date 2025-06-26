from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import TextElement
from model import PetModel
from agents import DogAgent, CatAgent, FeederAgent, FoodMarker, BusinessAgent

class PopulationText(TextElement):
    """
    Displays comprehensive ecosystem statistics.
    """
    def render(self, model):
        business_info = ""
        if model.business_agents_active > 0:
            business_info = f" | 🏢 Business: {model.business_agents_active}"
        
        return (f"Dogs: {model.dog_count} | Cats: {model.cat_count} | "
                f"Food: {model.food_count}{business_info}<br>"
                f"Births: {model.total_births} | "
                f"Harvested: {model.total_harvested} | Money: ${model.total_money_made}")

def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5, "Layer": 0, "Color": "grey"}

    # Add state text and age info for pets
    if hasattr(agent, "state"):
        if hasattr(agent, "age"):
            portrayal["text"] = f"{agent.state}\nAge:{agent.age}"
        else:
            portrayal["text"] = agent.state
        portrayal["text_color"] = "black"

    if isinstance(agent, DogAgent):
        portrayal["Shape"] = "static/img/dog.png"
        portrayal["Layer"] = 2
        portrayal["r"] = 1
        # Color code by hunger level
        if agent.hunger >= 20:
            portrayal["Color"] = "red"  # Very hungry
        elif agent.hunger >= 15:
            portrayal["Color"] = "orange"  # Hungry
        elif agent.reproduction_cooldown == 0 and agent.age >= 30:
            portrayal["Color"] = "pink"  # Ready to mate
        else:
            portrayal["Color"] = "brown"  # Normal
            
    elif isinstance(agent, CatAgent):
        portrayal["Shape"] = "static/img/cat.png"
        portrayal["Layer"] = 2
        portrayal["r"] = 1
        # Color code by hunger level
        if agent.hunger >= 18:
            portrayal["Color"] = "red"  # Very hungry
        elif agent.hunger >= 12:
            portrayal["Color"] = "orange"  # Hungry
        elif agent.reproduction_cooldown == 0 and agent.age >= 25:
            portrayal["Color"] = "pink"  # Ready to mate
        else:
            portrayal["Color"] = "gray"  # Normal
            
    elif isinstance(agent, BusinessAgent):
        portrayal["Shape"] = "static/img/businessman.png"  # Changed to use the businessman image
        portrayal["Layer"] = 3
        portrayal["r"] = 1.2
        portrayal["Color"] = "black"
        portrayal["text"] = f"💼\n${agent.money_earned}"
        portrayal["text_color"] = "white"
        
    elif isinstance(agent, FeederAgent):
        portrayal["Shape"] = "static/img/feeder.png"
        portrayal["Layer"] = 1
        portrayal["r"] = 1
        portrayal["Color"] = "blue"
        
    elif isinstance(agent, FoodMarker):
        portrayal["Shape"] = "static/img/food.png"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.5
        portrayal["text"] = ""
        # Food gets darker as it ages
        freshness = max(0, (100 - agent.age) / 100)
        green_value = int(255 * freshness)
        portrayal["Color"] = f"rgb(139, {green_value}, 69)"  # Brown to dark brown

    return portrayal

grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)
population_text = PopulationText()

server = ModularServer(
    PetModel,
    [grid, population_text],
    "Virtual Pet Ecosystem - Improved Version",
    {
        "width": 20,
        "height": 20,
        "num_dogs": 8,  
        "num_cats": 8,
        "num_feeders": 3 
    }
)