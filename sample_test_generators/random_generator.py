import time
from random import randint

import pandas as pd

from code_pipeline.tests_generation import RoadTestFactory
from time import sleep

import logging as log


class RandomTestGenerator():
    """
        This simple (naive) test generator creates roads using 4 points randomly placed on the map.
        We expect that this generator quickly creates plenty of tests, but many of them will be invalid as roads
        will likely self-intersect.
    """

    def __init__(self, executor=None, map_size=None):
        self.executor = executor
        self.map_size = map_size
        self.ROAD_POINTS = 4
        self.start_time = True
        self.budget = 0

        self.new_fitness = 0

        self.test_oob = []
        self.time = []
        self.time_remaining = 0

    def save_results(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        # Save the results to a file
        df = pd.DataFrame({'oob': self.test_oob, 'time': self.time})
        df.to_csv(f'./result2/random_generator_{timestamp}.csv')

    def random_road(self):
        road_points = []
        for i in range(0, self.ROAD_POINTS):
            road_points.append((randint(0, self.map_size), randint(0, self.map_size)))
        return road_points

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

        # Plot the OOB_Percentage: How much the car is outside the road?
        oob_percentage = [state.oob_percentage for state in execution_data]
        if test_outcome != 'INVALID':
            self.time.append(self.budget - self.time_remaining)
            if len(oob_percentage) > 0:
                log.info("Collected %d states information. Max is %.3f", len(oob_percentage), max(oob_percentage))
                self.new_fitness = max(oob_percentage)
            else:
                self.new_fitness = 0
            self.test_oob.append(self.new_fitness)

        log.info(f"Executed test {the_test.id}. Remaining time {time_remaining}")

        # Print the result from the test and continue
        log.info("test_outcome %s", test_outcome)
        log.info("description %s", description)

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
                # Pick up random points from the map. They will be interpolated anyway to generate the road
                road_points = self.random_road()
                self._execute(road_points)
        finally:
            self.save_results()
            log.info("Test generation is over")
