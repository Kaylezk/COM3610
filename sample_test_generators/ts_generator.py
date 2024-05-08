import time
from random import randint, choice

import numpy as np

from code_pipeline.tests_generation import RoadTestFactory
from time import sleep
import pandas as pd
import os

import logging as log


class TS():

    def __init__(self, executor=None, map_size=None):
        self.executor = executor
        self.map_size = map_size

        # road points
        self.road_points = []
        self.new_roads = []

        self.current_fitness = 0
        self.new_fitness = 0
        self.best_fitness = 0

        # tabu
        self.tabu_list = []
        self.tabu_tenure = 10

        # info
        self.test_oob = []

        self.time_remaining = 0
        self.time = []
        self.start_time = True
        self.budget = 0

        # flag
        self.flag = True
        self.init_flag = True

        # counter
        self.counter = 0
        self.count_list = []

        self.ROAD_POINTS = 4

    def save_results(self):
        # Save the results to a file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        df = pd.DataFrame({'counter': self.count_list, 'oob': self.test_oob, 'time': self.time})
        df.to_csv(f'./result2/ts_generator_{timestamp}.csv')

    # valid road
    def valid_road(self, road: list):
        self._execute(road)
        if not self.flag:
            self.flag = True
            return True
        return False

    def add_info(self):
        self.count_list.append(self.counter)
        self.test_oob.append(self.current_fitness)
        self.time.append(self.budget - self.time_remaining)

    def random_road(self):
        road_points = []
        for i in range(0, self.ROAD_POINTS):
            road_points.append((randint(0, self.map_size), randint(0, self.map_size)))
        return road_points

    def neighbor(self):
        neighbor = []
        tweak = choice([-30, -20, -10, 10, 20, 30])
        for i in range(0, self.ROAD_POINTS):
            neighbor.append((self.road_points[i][0] + tweak, self.road_points[i][1] + tweak))
        return neighbor

    def add_tabu(self, candidate: list):
        # find the next best candidate that is not in the tabu list
        for i in range(len(candidate)):
            if candidate[i][0] not in self.tabu_list or candidate[i][1] > self.best_fitness:
                self.tabu_list.append(candidate[i][0])
                self.road_points = candidate[i][0]
                self.current_fitness = candidate[i][1]

                # update best fitness
                if candidate[i][1] > self.best_fitness:
                    self.best_fitness = candidate[i][1]

                self.add_info()
                break

    def tabu_search(self):
        # candidate list
        candidate = []

        # counter
        self.counter += 1
        log.info(f"Currently executing candidate set number: {self.counter}")

        # generate 4 candidate solutions
        while len(candidate) < 3:
            self.new_roads = self.neighbor()
            if self.valid_road(self.new_roads):
                candidate.append((self.new_roads, self.new_fitness))

        # order the candidate list
        # [([road_points], fitness), ([road_points], fitness), ([road_points], fitness)]
        candidate = sorted(candidate, key=lambda x: x[1], reverse=True)

        # update the tabu list
        if len(self.tabu_list) < self.tabu_tenure:
            self.add_tabu(candidate)
        else:
            self.tabu_list.pop(0)
            self.add_tabu(candidate)

    def _execute(self, road_points):
        # Some more debugging
        log.info("Generated test using: %s", road_points)
        # Decorate the_test object with the id attribute
        the_test = RoadTestFactory.create_road_test(road_points)

        time_remaining = self.executor.get_remaining_time()["time-budget"]
        log.info(f"Simulated test generation for 0.3 sec. Remaining time {time_remaining}")
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
                # Some debugging
                time_remaining = self.executor.get_remaining_time()["time-budget"]
                log.info(f"Starting test generation. Remaining time {time_remaining}")

                # get the budget
                if self.start_time:
                    self.budget = time_remaining
                    self.start_time = False

                # Simulate the time to generate a new test
                sleep(0.5)

                if self.init_flag:
                    self.new_roads = self.random_road()
                    self._execute(self.new_roads)
                    # add initial test
                    if not self.flag:
                        log.info("Initial test")
                        self.init_flag = False

                        # update fitness
                        self.current_fitness = self.new_fitness
                        self.best_fitness = self.new_fitness

                        # update road points
                        self.road_points = self.new_roads

                        # add info
                        self.add_info()
                else:
                    log.info("ts test")
                    self.tabu_search()
        finally:
            self.save_results()
