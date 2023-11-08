from typing import Tuple, List, Union

import numpy as np


class TSP:
    def __init__(
            self,
            adjacency_matrix: np.ndarray,
    ):
        self.adjacency_matrix = adjacency_matrix # La matrice d'adjacence qui sera utilisée pour calculer le coût des chemins

    def get_solution(self) -> Union[Tuple, List[int], np.ndarray]:
        r"""
        Return a solution to the TSP problem.

        :Note: The list that is returned must be a cycle, i.e. the first and last elements must be the same.

        :return: A list of nodes representing a solution to the TSP problem.
        :rtype: Union[Tuple, List[int], np.ndarray]
        """
        cycle = [0]
        visited_cities = [0]
        nb_of_cities = self.adjacency_matrix.shape[0]

        i = 0
        while i < nb_of_cities-1:
            closest_cities = self.find_closest_cities(starting_city=i, visited_cities=visited_cities)
            cycle.append(closest_cities[0])
            i = closest_cities[0]
            visited_cities.append(i)

        cycle.append(0)

        #path = np.random.permutation(self.adjacency_matrix.shape[0])
        #cycle = np.concatenate((path, [path[0]]))
        return cycle

    def find_closest_cities(self, starting_city:int, visited_cities:list):
        """
        From the city starting_city, find the closest city that hasn't been visited yet.
        visited_cities is a list that saves the previously visited cities.
        Returns the closest city of starting_city. 
        """

        unvisited_cities = np.delete(self.adjacency_matrix[starting_city], visited_cities)
        zero_distance_to_10 = np.where(unvisited_cities > 0, unvisited_cities, unvisited_cities + 10)
        min_distance = np.amin(zero_distance_to_10)
        closest_cities = np.where(self.adjacency_matrix[starting_city] == min_distance)[0]
        return closest_cities



if __name__ == "__main__":
    villes = np.array([[0,1,2,3],[1,0,4,5],[2,4,0,6],[3,5,6,0]])
    print(villes)
    tsp = TSP(villes)
    cycle = tsp.get_solution()
    print(cycle)






