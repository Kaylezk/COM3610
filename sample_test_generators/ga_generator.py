import time
from random import randint, uniform, random, choices

import numpy as np
import pandas as pd

from code_pipeline.tests_generation import RoadTestFactory
from time import sleep

import logging as log


class GA():

    def __init__(self, executor=None, map_size=None):
        self.executor = executor
        self.map_size = map_size

        # road points
        self.road_points = []
        self.new_roads = []
        self.new_fitness = 0
        self.ROAD_POINTS = 4

        # population
        self.POPULATION_SIZE = 10
        self.population = []

        # crossover
        self.CROSSOVER_RATE = 0.8
        # mutation
        self.MUTATION_RATE = 0.3

        # generation
        self.generations = []
        self.current_generation = 1

        # info
        self.test_oob = []

        self.time_remaining = 0
        self.time = []

        self.start_time = True
        self.budget = 0

        # flag
        self.flag = True
        self.is_init = True

    def save_results(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        # Save the results to a file
        df = pd.DataFrame({'generation': self.generations, 'oob': self.test_oob, 'time': self.time})
        df.to_csv(f'./result2/ga_generator_{timestamp}.csv', index=False)

    # valid road
    def valid_road(self, road: list):
        self._execute(road)
        if not self.flag:
            self.flag = True
            return True
        return False

    # random road points
    def random_road(self):
        road_points = []
        for i in range(0, self.ROAD_POINTS):
            road_points.append((randint(0, self.map_size), randint(0, self.map_size)))
        return road_points

    def add_info(self):
        self.test_oob.append(self.new_fitness)
        self.time.append(self.budget - self.time_remaining)
        self.generations.append(self.current_generation)

    # population -> [(road1, fitness1), (road1, fitness1), (road1, fitness1)]
    def init_population(self):
        while len(self.population) < self.POPULATION_SIZE:
            road = self.random_road()
            if self.valid_road(road):
                self.population.append((road, self.new_fitness))
                self.add_info()

    def selection(self):
        # Roulette wheel selection
        # avoid zero fitness values
        min_prob = 0.0001
        total_fitness = sum([fit for _, fit in self.population])
        min_adjustment = min_prob * len(self.population)
        fitness_prob = [fit / total_fitness * (1 - min_adjustment) + min_adjustment for _, fit in self.population]

        cumulative_probs = np.cumsum(fitness_prob)

        # select new parents
        for i, individual in enumerate(self.population):
            r = random()
            if r < cumulative_probs[i]:
                return individual[0]

    # parents1, parents2 -> [point1, point2, point3]
    def crossover(self, parents1, parents2):
        if self.CROSSOVER_RATE > random():
            crossover_point = randint(0, self.ROAD_POINTS)
            child1 = parents1[:crossover_point] + parents2[crossover_point:]
            child2 = parents2[:crossover_point] + parents1[crossover_point:]
            return child1, child2
        else:
            return parents1, parents2

    # individual -> [point1, point2, point3]
    def mutation(self, individual):
        tweak = randint(-20, 20)
        for i in range(len(individual)):
            if self.MUTATION_RATE > random():
                individual[i] = (individual[i][0] + tweak, individual[i][1] + tweak)

        return individual

    def ga(self):
        new_population = []
        if self.is_init:
            self.init_population()
            self.is_init = False

        self.current_generation += 1

        # keep the top 3
        # top_3 = sorted(self.population, key=lambda x: x[1], reverse=True)[:3]

        # new_population.extend(top_3)

        while len(new_population) < self.POPULATION_SIZE:
            # selection
            parents1 = self.selection()
            parents2 = self.selection()

            # crossover and mutation
            child1, child2 = self.crossover(parents1, parents2)
            for individual in [self.mutation(child1), self.mutation(child2)]:
                if self.valid_road(individual):
                    new_population.append((individual, self.new_fitness))
                    self.add_info()

        # record the top 3
        # for i in top_3:
        #     self.test_oob.append(i[1])
        #     self.time.append(self.budget - self.time_remaining)
        #     self.generations.append(self.current_generation)

        self.population = new_population

    def _execute(self, road_points):
        # Some more debugging
        log.info("Generated test using: %s", road_points)
        # Decorate the_test object with the id attribute
        the_test = RoadTestFactory.create_road_test(road_points)

        time_remaining = self.executor.get_remaining_time()["time-budget"]
        log.info(f"Simulated test generation for 0.5 sec. Remaining time {time_remaining}")

        # Try to execute the test
        test_outcome, description, execution_data = self.executor.execute_test(the_test)
        time_remaining = self.executor.get_remaining_time()["time-budget"]
        self.time_remaining = time_remaining
        log.info(f"Executed test {the_test.id}. Remaining time {time_remaining}")

        # Print the result from the test and continue
        log.info("test_outcome %s", test_outcome)
        log.info("description %s", description)

        if test_outcome != 'INVALID':
            self.flag = False
            oob_percentage = [state.oob_percentage for state in execution_data]
            if len(oob_percentage) > 0:
                log.info("Collected %d states information. Max is %.3f", len(oob_percentage), max(oob_percentage))
                self.new_fitness = max(oob_percentage)
            else:
                self.new_fitness = 0

    def start(self):
        try:
            while not self.executor.is_over():
                time_remaining = self.executor.get_remaining_time()["time-budget"]
                log.info(f"Starting test generation. Remaining time {time_remaining}")

                # get the budget
                if self.start_time:
                    self.budget = time_remaining
                    self.start_time = False

                # Simulate the time to generate a new test
                sleep(0.5)
                self.ga()
        finally:
            self.save_results()
