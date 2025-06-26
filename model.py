from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from agents import DogAgent, CatAgent, FeederAgent, FoodMarker, BusinessAgent

class PetModel(Model):
    def __init__(self, width=20, height=20, num_dogs=3, num_cats=3, num_feeders=1):
        super().__init__()
        
        self.grid = MultiGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.running = True
        self.next_agent_id = 0

        # Attributes to hold current population counts
        self.dog_count = 0
        self.cat_count = 0
        self.food_count = 0
        self.feeder_count = 0
        self.business_agents_active = 0
        
        # Business thresholds - changed to 30 for both species
        self.dog_harvest_threshold = 30
        self.cat_harvest_threshold = 30
        self.max_business_agents = 2
        
        # Track statistics
        self.step_count = 0
        self.total_births = 0
        self.total_deaths = 0
        self.total_harvested = 0
        self.total_money_made = 0

        # Create dogs
        for _ in range(num_dogs):
            dog = DogAgent(self.next_agent_id, self)
            self.place_agent_on_empty(dog)
            self.next_agent_id += 1

        # Create cats
        for _ in range(num_cats):
            cat = CatAgent(self.next_agent_id, self)
            self.place_agent_on_empty(cat)
            self.next_agent_id += 1
            
        # Create feeders
        for _ in range(num_feeders):
            feeder = FeederAgent(self.next_agent_id, self)
            self.place_agent_on_empty(feeder)
            self.next_agent_id += 1

    def place_agent_on_empty(self, agent):
        """Place agent on an empty cell or find the least crowded cell"""
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            
            # Check if cell is empty
            if self.grid.is_cell_empty((x, y)):
                self.grid.place_agent(agent, (x, y))
                self.schedule.add(agent)
                return
            
            attempts += 1
        
        # If no empty cell found, place on least crowded cell
        min_agents = float('inf')
        best_pos = None
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                cell_contents = self.grid.get_cell_list_contents([(x, y)])
                if len(cell_contents) < min_agents:
                    min_agents = len(cell_contents)
                    best_pos = (x, y)
        
        if best_pos:
            self.grid.place_agent(agent, best_pos)
            self.schedule.add(agent)

    def step(self):
        self.step_count += 1
        
        # Store previous counts to track births/deaths
        prev_dog_count = self.dog_count
        prev_cat_count = self.cat_count
        
        # Run agent steps
        self.schedule.step()
        
        # Recalculate counts each step
        self.dog_count = sum(1 for a in self.schedule.agents if isinstance(a, DogAgent))
        self.cat_count = sum(1 for a in self.schedule.agents if isinstance(a, CatAgent))
        self.food_count = sum(1 for a in self.schedule.agents if isinstance(a, FoodMarker))
        self.feeder_count = sum(1 for a in self.schedule.agents if isinstance(a, FeederAgent))
        self.business_agents_active = sum(1 for a in self.schedule.agents if isinstance(a, BusinessAgent))
        
        # Check if we need to spawn business agents
        self.check_business_intervention()
        
        # Track births and deaths
        dog_births = max(0, self.dog_count - prev_dog_count)
        cat_births = max(0, self.cat_count - prev_cat_count)
        self.total_births += dog_births + cat_births
        
        dog_deaths = max(0, prev_dog_count - self.dog_count)
        cat_deaths = max(0, prev_cat_count - self.cat_count)
        self.total_deaths += dog_deaths + cat_deaths
        
        # Optional: Print statistics every 50 steps
        if self.step_count % 50 == 0:
            print(f"Step {self.step_count}: Dogs={self.dog_count}, Cats={self.cat_count}, "
                  f"Food={self.food_count}, Business=${self.business_agents_active}")
            print(f"  Births={self.total_births}, Deaths={self.total_deaths}, "
                  f"Harvested={self.total_harvested}, Money=${self.total_money_made}")
        
        # Stop simulation if all pets die
        if self.dog_count == 0 and self.cat_count == 0:
            print(f"All pets died at step {self.step_count}")
            self.running = False

    def check_business_intervention(self):
        """Spawn targeted business agents when populations get too high"""
        if self.business_agents_active >= self.max_business_agents:
            return
            
        spawn_business = False
        target_species = None
        reason = ""
        
        # Check if dogs need harvesting
        if self.dog_count >= self.dog_harvest_threshold:
            spawn_business = True
            target_species = 'dog'
            reason = f"dog overpopulation ({self.dog_count})"
        # Check if cats need harvesting (only if dogs don't need it)
        elif self.cat_count >= self.cat_harvest_threshold:
            spawn_business = True
            target_species = 'cat'
            reason = f"cat overpopulation ({self.cat_count})"
        
        if spawn_business:
            # Create business agent that targets specific species
            business_agent = BusinessAgent(self.next_agent_id, self, target_species=target_species)
            self.place_agent_on_empty(business_agent)
            self.next_agent_id += 1
            self.business_agents_active += 1
            print(f"🏢 BusinessAgent {business_agent.unique_id} enters to harvest {target_species}s due to {reason}!")