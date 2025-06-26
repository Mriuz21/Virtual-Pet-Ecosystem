from mesa import Agent
import random

class PetAgent(Agent):
    def __init__(self, unique_id, model, max_age_range, repro_chance, repro_cooldown):
        super().__init__(unique_id, model)
        self.age = 0
        self.max_age = random.randint(*max_age_range)
        self.reproduction_chance = repro_chance
        self.reproduction_cooldown_period = repro_cooldown
        self.reproduction_cooldown = 0

    def update_vitals_and_age(self):
        self.age += 1
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1

        
        if self.random.random() < 0.1:  
            self.hunger = min(self.max_hunger, self.hunger + 1)

    def get_nearby_agents(self, agent_type, radius=1):
        if self.pos is None:
            return []
        all_neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=radius)
        return [agent for agent in all_neighbors if isinstance(agent, agent_type)]

    def move_towards(self, target_pos):
        # Check if agent is still on the grid
        if self.pos is None:
            return
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        step_x = 0 if dx == 0 else dx // abs(dx)
        step_y = 0 if dy == 0 else dy // abs(dy)
        new_pos = (self.pos[0] + step_x, self.pos[1] + step_y)
        self.model.grid.move_agent(self, new_pos)

    def distance_to(self, other_agent):
        # Check if both agents are still on the grid
        if self.pos is None or other_agent.pos is None:
            return float('inf')
        return max(abs(self.pos[0] - other_agent.pos[0]), abs(self.pos[1] - other_agent.pos[1]))

    def random_move(self):
        # Check if agent is still on the grid
        if self.pos is None:
            return
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)


class DogAgent(PetAgent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model, max_age_range=(200, 250), repro_chance=0.4, repro_cooldown=8)
        self.hunger = 3  
        self.energy = 8  
        self.state = "idle"
        self.max_hunger = 30  
        self.health = 100

    def step(self):
       
        if self.pos is None:
            return

        if self.hunger >= self.max_hunger or self.age >= self.max_age or self.health <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
        if self.hunger >= 22:  
            self.state = "seeking_food"
            self.seek_food()
        elif self.energy <= 1: 
            self.state = "resting"
            self.rest()
        elif (self.hunger <= 18 and self.energy >= 3 and 
              self.reproduction_cooldown == 0 and self.age >= 25): 
            self.state = "seeking_mate"
            self.seek_mate()
        elif self.hunger >= 12: 
            self.state = "seeking_food"
            self.seek_food()
        else:
            self.state = "playing"
            self.play()

        if self.random.random() < 0.5:  
            self.energy = max(0, self.energy - 1)
        
        self.update_vitals_and_age()

    def seek_food(self):
        nearby_food = self.get_nearby_agents(FoodMarker, radius=10)  
        if nearby_food:
            food_to_get = min(nearby_food, key=lambda f: self.distance_to(f))
            self.move_towards(food_to_get.pos)
            if self.pos == food_to_get.pos:
                self.eat(food_to_get)
        else:
            self.random_move()

    def eat(self, food):
        self.model.grid.remove_agent(food)
        self.model.schedule.remove(food)
        self.hunger = max(0, self.hunger - 15)  
        self.energy = min(10, self.energy + 3)  
        self.health = min(100, self.health + 8) 
        self.state = "eating"

    def rest(self):
        self.energy = min(10, self.energy + 4)  
        self.health = min(100, self.health + 2) 

    def play(self):
        self.random_move()

    def seek_mate(self):
        nearby_partners = self.get_nearby_agents(DogAgent, radius=12) 
        # Even more lenient partner requirements
        ready_partners = [p for p in nearby_partners if 
                         p.reproduction_cooldown == 0 and 
                         p.hunger <= 20 and  # More lenient
                         p.age >= 25 and  # Lower maturity age
                         p.unique_id != self.unique_id]  
        
        if ready_partners:
            partner = min(ready_partners, key=lambda p: self.distance_to(p))
            if self.distance_to(partner) <= 1:
                self.try_reproduce_with(partner)
            else:
                self.move_towards(partner.pos)
        else:
            
            if self.hunger >= 8:
                self.seek_food()
            else:
                self.random_move()

    def try_reproduce_with(self, partner):
        if self.random.random() < self.reproduction_chance:
            self.reproduction_cooldown = self.reproduction_cooldown_period
            partner.reproduction_cooldown = partner.reproduction_cooldown_period

            
            self.energy = max(0, self.energy - 2)
            self.hunger = min(self.max_hunger - 1, self.hunger + 2)
            partner.energy = max(0, partner.energy - 2)
            partner.hunger = min(partner.max_hunger - 1, partner.hunger + 2)

            offspring_type = type(self)
            offspring = offspring_type(self.model.next_agent_id, self.model)

            self.model.next_agent_id += 1
            
            # Try to place offspring nearby
            possible_positions = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True)
            for pos in possible_positions:
                if self.model.grid.is_cell_empty(pos):
                    self.model.grid.place_agent(offspring, pos)
                    self.model.schedule.add(offspring)
                    print(f"Dog {self.unique_id} mated with {partner.unique_id} - offspring {offspring.unique_id}")
                    return
            
            # If no empty space nearby, place randomly
            self.model.place_agent_on_empty(offspring)
            print(f"Dog {self.unique_id} mated with {partner.unique_id} - offspring {offspring.unique_id}")


class CatAgent(PetAgent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model, max_age_range=(190, 230), repro_chance=0.25, repro_cooldown=20)
        self.hunger = 2  
        self.sleepiness = 4  
        self.state = "idle"
        self.max_hunger = 32  
        self.health = 100

    def step(self):
        if self.pos is None:
            return
        if self.hunger >= self.max_hunger or self.age >= self.max_age or self.health <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
        if self.hunger >= 24:  
            self.state = "seeking_food"
            self.seek_food()
        elif self.sleepiness >= 9:  
            self.state = "sleeping"
            self.sleep()
        elif (self.hunger <= 15 and self.sleepiness <= 5 and 
              self.reproduction_cooldown == 0 and self.age >= 40):  
            self.state = "seeking_mate"
            self.seek_mate()
        elif self.hunger >= 14:
            self.state = "seeking_food"
            self.seek_food()
        elif self.sleepiness >= 7:
            self.state = "sleeping"
            self.sleep()
        else:
            self.state = "wandering"
            self.wander()

        
        if self.random.random() < 0.4:  
            self.sleepiness = min(10, self.sleepiness + 1)
        
        self.update_vitals_and_age()

    def seek_food(self):
        nearby_food = self.get_nearby_agents(FoodMarker, radius=10)
        if nearby_food:
            food_to_get = min(nearby_food, key=lambda f: self.distance_to(f))
            self.move_towards(food_to_get.pos)
            if self.pos == food_to_get.pos:
                self.eat(food_to_get)
        else:
            self.random_move()

    def eat(self, food):
        self.model.grid.remove_agent(food)
        self.model.schedule.remove(food)
        self.hunger = max(0, self.hunger - 18)  # Even more effective eating
        self.health = min(100, self.health + 5)
        self.state = "eating"

    def sleep(self):
        self.sleepiness = max(0, self.sleepiness - 5)  # Better sleep recovery
        self.health = min(100, self.health + 3)  # Sleep improves health more

    def wander(self):
        self.random_move()

    def seek_mate(self):
        nearby_partners = self.get_nearby_agents(CatAgent, radius=12)
        ready_partners = [p for p in nearby_partners if 
                         p.reproduction_cooldown == 0 and 
                         p.hunger <= 15 and 
                         p.sleepiness <= 5 and  
                         p.age >= 40 and  #
                         p.unique_id != self.unique_id]
        
        if ready_partners:
            partner = min(ready_partners, key=lambda p: self.distance_to(p))
            if self.distance_to(partner) <= 1:
                self.try_reproduce_with(partner)
            else:
                self.move_towards(partner.pos)
        else:
            if self.hunger >= 10:
                self.seek_food()
            else:
                self.random_move()

    def try_reproduce_with(self, partner):
        if self.random.random() < self.reproduction_chance:
            self.reproduction_cooldown = self.reproduction_cooldown_period
            partner.reproduction_cooldown = partner.reproduction_cooldown_period

            # Higher reproduction costs for cats
            self.hunger = min(self.max_hunger - 1, self.hunger + 5)
            self.sleepiness = min(10, self.sleepiness + 3)
            partner.hunger = min(partner.max_hunger - 1, partner.hunger + 5)
            partner.sleepiness = min(10, partner.sleepiness + 3)

            offspring_type = type(self)
            offspring = offspring_type(self.model.next_agent_id, self.model)

            self.model.next_agent_id += 1
            
            possible_positions = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True)
            for pos in possible_positions:
                if self.model.grid.is_cell_empty(pos):
                    self.model.grid.place_agent(offspring, pos)
                    self.model.schedule.add(offspring)
                    print(f"Cat {self.unique_id} mated with {partner.unique_id} - offspring {offspring.unique_id}")
                    return
            
            self.model.place_agent_on_empty(offspring)
            print(f"Cat {self.unique_id} mated with {partner.unique_id} - offspring {offspring.unique_id}")


class FeederAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.drop_rate = 0.4 
        self.state = "patrolling"
        self.food_dropped_count = 0
        self.cooldown = 0
        self.max_cooldown = 8  

    def step(self):
        if self.cooldown > 0:
            self.state = f"cooldown ({self.cooldown})"
            self.cooldown -= 1
            return

        self.state = "patrolling"
        self.patrol()
        if self.random.random() < self.drop_rate:
            self.drop_food()

    def patrol(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def drop_food(self):
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        if not any(isinstance(obj, FoodMarker) for obj in cell_contents):
            food_item = FoodMarker(self.model.next_agent_id, self.model)
            self.model.grid.place_agent(food_item, self.pos)
            self.model.schedule.add(food_item)
            self.model.next_agent_id += 1

            self.food_dropped_count += 1
            if self.food_dropped_count >= 10:
                self.food_dropped_count = 0
                self.cooldown = self.max_cooldown


class BusinessAgent(Agent):
    def __init__(self, unique_id, model, target_species=None):
        super().__init__(unique_id, model)
        self.state = "hunting"
        self.money_earned = 0
        self.animals_collected = 0
        self.hunt_radius = 20  
        self.collection_target = 10  
        self.max_steps = 5 
        self.steps_taken = 0
        self.price_per_dog = random.randint(3, 6)  
        self.price_per_cat = random.randint(2, 4)
        self.target_species = target_species  
        
        print(f"BusinessAgent {self.unique_id} targeting {target_species}s for harvest")

    def step(self):
        self.steps_taken += 1
        
        
        if self.steps_taken >= self.max_steps or self.animals_collected >= self.collection_target:
            self.state = f"leaving (${self.money_earned} earned, {self.animals_collected} collected)"
            self.leave_ecosystem()
            return

       
        self.hunt_target_animals()

    def hunt_target_animals(self):
       
        if self.target_species == 'dog':
            targets = self.get_nearby_agents(DogAgent, radius=self.hunt_radius)
        elif self.target_species == 'cat':
            targets = self.get_nearby_agents(CatAgent, radius=self.hunt_radius)
        else:
            targets = []
        
        if not targets:
            self.state = f"searching for {self.target_species}s (no targets found)"
            self.random_move()
            return

       
        captured_this_step = 0
        max_captures_per_step = 3
        
       
        targets.sort(key=lambda x: self.distance_to(x))
        
        for target in targets:
            if self.animals_collected >= self.collection_target:
                break
            if captured_this_step >= max_captures_per_step:
                break
                
           
            if self.distance_to(target) <= self.hunt_radius:
                if self.distance_to(target) > 1:
                    self.move_towards(target.pos)
                
                
                if self.distance_to(target) <= 1:
                    if self.attempt_capture(target):
                        captured_this_step += 1
        
        if captured_this_step == 0:
            self.state = f"hunting {self.target_species}s"
        else:
            self.state = f"captured {captured_this_step} {self.target_species}s this step"

    def attempt_capture(self, target):
        
        if self.random.random() < 0.9:  # 90% success rate
            if isinstance(target, DogAgent):
                price = self.price_per_dog
                animal_type = "Dog"
            else:
                price = self.price_per_cat
                animal_type = "Cat"
            
            self.money_earned += price
            self.animals_collected += 1
            
            # Update model statistics
            self.model.total_harvested += 1
            self.model.total_money_made += price
            
            # Remove the animal from the ecosystem
            self.model.grid.remove_agent(target)
            self.model.schedule.remove(target)
            
            print(f"💼 BusinessAgent {self.unique_id} captured {animal_type} {target.unique_id} for ${price} (Total: {self.animals_collected}/{self.collection_target})")
            return True
        else:
            print(f"BusinessAgent {self.unique_id} failed to capture {type(target).__name__} {target.unique_id}")
            return False

    def leave_ecosystem(self):
        # Business agent leaves after completing mission
        print(f"BusinessAgent {self.unique_id} is leaving after {self.steps_taken} steps with {self.animals_collected} {self.target_species}s, earned ${self.money_earned}")
        if self in self.model.schedule.agents:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.business_agents_active -= 1

    def get_nearby_agents(self, agent_type, radius=1):
        all_neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=radius)
        return [agent for agent in all_neighbors if isinstance(agent, agent_type)]

    def distance_to(self, other_agent):
        return max(abs(self.pos[0] - other_agent.pos[0]), abs(self.pos[1] - other_agent.pos[1]))

    def move_towards(self, target_pos):
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        step_x = 0 if dx == 0 else dx // abs(dx)
        step_y = 0 if dy == 0 else dy // abs(dy)
        new_pos = (self.pos[0] + step_x, self.pos[1] + step_y)
        self.model.grid.move_agent(self, new_pos)

    def random_move(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)


class FoodMarker(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.expiration_time = 75
        self.age = 0

    def step(self):
        self.age += 1
        if self.age >= self.expiration_time:
            if self in self.model.schedule.agents:  
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)