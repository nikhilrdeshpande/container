from deap import base, creator, tools, algorithms
import random

def genetic_algorithm(data):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    
    def eval_sequence(individual):
        total_weight = 0
        total_moves = 0
        weight_distribution = 0
        for idx in individual:
            container = data.iloc[idx]
            total_weight += container['Weight']
            total_moves += container['Length'] * container['Width']
            # Assuming location is in the form 'row,column'
            try:
                location = container['Location'].split(',')
                weight_distribution += abs(int(location[0]) - int(location[1])) * container['Weight']
            except:
                pass  # Skip invalid location formats
        # Combine different aspects into a single fitness value
        return total_weight + total_moves + weight_distribution,

    toolbox = base.Toolbox()
    toolbox.register("indices", random.sample, range(len(data)), len(data))
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("evaluate", eval_sequence)
    
    population = toolbox.population(n=300)
    algorithms.eaSimple(population, toolbox, cxpb=0.5, mutpb=0.2, ngen=40, verbose=False)
    
    best_individual = tools.selBest(population, k=1)[0]
    return best_individual