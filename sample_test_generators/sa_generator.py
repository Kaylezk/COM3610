import math
from random import randint, uniform, random
from code_pipeline.tests_generation import RoadTestFactory
from time import sleep

import logging as log


class SA():

    def __init__(self, executor=None, map_size=None):
        self.executor = executor
        self.map_size = map_size
        self.flag = True
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

    def neighbor(self, road_points):
        neighbor_points = []
        tweak = randint(-2, 2)
        for i in range(0, 3):
            road_points[i] = (road_points[i][0] + tweak, road_points[i][1] + tweak)
        for j in road_points:
            neighbor_points.append(j)
        return neighbor_points

    def sa(self):
        initial_temperature = 100
        cooling_rate = 10

        while initial_temperature > 0:

            for i in range(0, 2):
                self.new_roads = self.neighbor(self.road_points)
                self._execute(self.new_roads)

                energy_difference = self.new_fitness - self.current_fitness

                if self.new_fitness > self.current_fitness or random() > math.exp(
                        -abs(energy_difference) / initial_temperature):
                    self.current_fitness = self.new_fitness
                    self.road_points = self.new_roads

                if self.current_fitness > self.best_fitness:
                    self.best_fitness = self.current_fitness
                    self.best_points = self.road_points

            initial_temperature -= cooling_rate

        return self.best_points

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
        log.info(f"Executed test {the_test.id}. Remaining time {time_remaining}")

        oob_percentage = [state.oob_percentage for state in execution_data]
        if len(oob_percentage) > 0:
            log.info("Collected %d states infomation. Max is %.3f", len(oob_percentage), max(oob_percentage))

        # Print the result from the test and continue
        log.info("test_outcome %s", test_outcome)
        log.info("description %s", description)

        if test_outcome != 'INVALID':
            self.flag = False
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
            if self.flag:
                self.new_roads = self.random_road()
                self._execute(self.new_roads)
                self.current_fitness = self.new_fitness
                self.road_points = self.new_roads
                self.best_points = self.road_points
            else:
                self.sa()
