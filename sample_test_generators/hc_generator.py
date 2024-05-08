import time
from random import randint

import pandas as pd

from code_pipeline.tests_generation import RoadTestFactory
from time import sleep

import logging as log


class HC():

    def __init__(self, executor=None, map_size=None):
        self.ROAD_POINTS = 4
        self.executor = executor
        self.map_size = map_size

        self.init_flag = True
        self.valid_flag = True

        self.road_points = []
        self.new_roads = []

        self.current_fitness = 0
        self.new_fitness = 0

        # info
        self.test_oob = []
        self.time_remaining = 0
        self.time = []

        self.start_time = True
        self.budget = 0

    def save_results(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        # Save the results to a file
        df = pd.DataFrame({'oob': self.test_oob, 'time': self.time})
        df.to_csv(f'./result2/hc_generator_{timestamp}.csv')

    def add_info(self):
        self.test_oob.append(self.new_fitness)
        self.time.append(self.budget - self.time_remaining)

    def random_road(self):
        road_points = []
        for i in range(0, self.ROAD_POINTS):
            road_points.append((randint(0, self.map_size), randint(0, self.map_size)))
        return road_points

    # neighbor road points
    def neighbor(self):
        neighbor = []
        tweak = randint(-20, 20)
        for i in range(0, self.ROAD_POINTS):
            neighbor.append((self.road_points[i][0] + tweak, self.road_points[i][1] + tweak))
        return neighbor

    def hill_climb(self):
        self.new_roads = self.neighbor()
        self._execute(self.new_roads)

        if self.new_fitness > self.current_fitness:
            self.current_fitness = self.new_fitness
            self.road_points = self.new_roads
            self.add_info()

    def _execute(self, road_points):
        # Some more debugging
        log.info("Generated test using: %s", road_points)
        # Decorate the_test object with the id attribute
        the_test = RoadTestFactory.create_road_test(road_points)

        time_remaining = self.executor.get_remaining_time()["time-budget"]
        log.info(f"Simulated test generation for 0.3 sec. Remaining time {time_remaining}")
        # Try to execute the test
        test_outcome, description, execution_data = self.executor.execute_test(the_test)

        # Get the remaining time
        time_remaining = self.executor.get_remaining_time()["time-budget"]
        self.time_remaining = time_remaining
        log.info(f"Executed test {the_test.id}. Remaining time {time_remaining}")

        # Print the result from the test and continue
        log.info("test_outcome %s", test_outcome)
        log.info("description %s", description)

        oob_percentage = [state.oob_percentage for state in execution_data]

        if test_outcome != 'INVALID':
            self.valid_flag = False
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

                sleep(0.5)

                # first test
                if self.init_flag:
                    self.new_roads = self.random_road()
                    self._execute(self.new_roads)

                    # initial test
                    if not self.valid_flag:
                        self.init_flag = False
                        self.current_fitness = self.new_fitness
                        self.road_points = self.new_roads
                        self.add_info()
                else:
                    self.hill_climb()
        finally:
            self.save_results()
