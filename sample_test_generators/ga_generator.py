from random import randint, uniform, random, choices
from code_pipeline.tests_generation import RoadTestFactory
from time import sleep

import logging as log


class GA():

    def __init__(self, executor=None, map_size=None):
        self.executor = executor
        self.map_size = map_size
        self.flag = True
        self.population = []
        self.fitness = []
        self.road_points = []
        self.new_roads = []
        self.best_points = []
        self.best_fitness = 0
        self.current_fitness = 0
        self.new_fitness = 0

    def random_road(self):
        road_points = []
        for i in range(0, 3):
            road_points.append((randint(0, self.map_size), randint(0, self.map_size)))
        return road_points

    def init_population(self):
        for i in range(0, 16):
            new_road = self.random_road()
            self.population.append(new_road)
        self.flag = False
        return self.population

    def crossover(self, population):
        # uniform crossover
        parent1 = []
        parent2 = []
        child1 = []
        child2 = []

        for i in range(0, 2):
            if len(population) > 1:
                parent1 = population[randint(0, len(population) - 1)]
                parent2 = population[randint(0, len(population) - 1)]
            else:
                return population

        crossover_prob = 0.5

        for gene1, gene2 in zip(parent1, parent2):
            if random() < crossover_prob:
                child1.append(gene1)
                child2.append(gene2)
            else:
                child1.append(gene2)
                child2.append(gene1)

        population.append(child1)
        population.append(child2)
        return population

    def mutation(self, population):
        tweak = randint(-2, 2)
        if len(population) == 0:
            return population
        random_road = randint(0, len(population) - 1)
        for i in range(0, len(population)):
            for j in range(3):
                population[random_road][j] = (
                    population[random_road][j][0] + tweak, population[random_road][j][1] + tweak)
        return population

    def selection(self, population):
        self.fitness = []
        selected_parents = []
        for i in range(len(population)):
            self._execute(population[i])
            self.fitness.append(self.new_fitness)
        total_fitness = sum(self.fitness)
        selected_prob = [fit / total_fitness for fit in self.fitness]

        for j in range(len(population)):
            if random() < selected_prob[j]:
                selected_parents.append(population[j])
        print(selected_parents)

        return selected_parents

    # def max_fitness(self, population):
    #     fitness = []
    #     for i in population:
    #         fitness.append(self.fitness(self.road_to_value(i)))
    #     max_index = fitness.index(max(fitness))
    #
    #     return population[max_index]

    def ga(self):
        if self.flag:
            self.population = self.init_population()
        selected_parents = self.selection(self.population)
        for i in range(0, 5):
            self.population = self.crossover(selected_parents)
            self.population = self.mutation(self.population)

    def _execute(self, road_points):
        flag = True
        # Some more debugging
        log.info("Generated test using: %s", road_points)
        # Decorate the_test object with the id attribute
        the_test = RoadTestFactory.create_road_test(road_points)

        time_remaining = self.executor.get_remaining_time()["time-budget"]
        log.info(f"Simulated test generation for 0.3 sec. Remaining time {time_remaining}")
        # Try to execute the test
        test_outcome, description, execution_data = self.executor.execute_test(the_test)
        time_remaining = self.executor.get_remaining_time()["time-budget"]
        log.info(f"Executed test {the_test.id}. Remaining time {time_remaining}")

        oob_percentage = [state.oob_percentage for state in execution_data]
        if len(oob_percentage) > 0:
            log.info("Collected %d states infomation. Max is %.3f", len(oob_percentage), max(oob_percentage))

        # Print the result from the test and continue
        log.info("test_outcome %s", test_outcome)
        log.info("description %s", description)

        # if test_outcome != 'INVALID':
        #     flag = False
        if test_outcome == 'PASS' or test_outcome == 'FAIL':
            self.new_fitness = max(oob_percentage)

    def start(self):
        while not self.executor.is_over():
            # Some debugging
            time_remaining = self.executor.get_remaining_time()["time-budget"]
            log.info(f"Starting test generation. Remaining time {time_remaining}")

            # Simulate the time to generate a new test
            sleep(0.5)
            # Pick up random points from the map. They will be interpolated anyway to generate the road
            self.ga()
