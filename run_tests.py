import os
import pickle
import sys
import warnings
from importlib import import_module

import pythonbasictools as pbt

from tools.tester import PerformanceTestCase, Tester, PEP8TestCase, CheckNotAllowedLibrariesTestCase


def get_data(data_file_path: str = "./data/data.pkl"):
    """
    This function downloads the data from Google Drive if it is not already present. You can run this function to
    download and inspect the data before running the tests.

    :param data_file_path: The path to the data file.
    :return: The data.
    :return: The data.
    """
    if os.path.exists(data_file_path):
        return pickle.load(open(data_file_path, "rb"))

    pbt.google_drive.GoogleDriveDownloader(
        file_id="1R8TF0BdUbKF-Z6yiDPNFIFo91ewvPxF2",
        dest_path=data_file_path,
    ).download()
    return pickle.load(open(data_file_path, "rb"))


def main(root_folder: str, data_file_path: str = "./data/data.pkl"):
    tester = Tester()
    pep8_test = PEP8TestCase(name="PEP8", file_path="./tsp.py")
    tester.add_test(pep8_test)
    lib_tester = CheckNotAllowedLibrariesTestCase(
        name="Check not allowed libraries",
        path=root_folder,
        not_allowed_libraries=["networkx"],
        excluded_folders=[os.path.join(root_folder, "venv"), os.path.join(root_folder, "__pycache__")],
    )
    tester.add_test(lib_tester)
    data = get_data(data_file_path=data_file_path)
    cwd = os.getcwd()
    print(f"Working directory: {os.getcwd()}")

    filename = f".tsp"
    file_root_importlike = root_folder.replace('./', '').replace('/', '.')
    cls_to_test = getattr(import_module(filename, file_root_importlike), "TSP")

    os.chdir(root_folder)
    performance_test = PerformanceTestCase(
        name=f"Performance Test on {len(data)} graphs",
        cls_to_test=cls_to_test,
        constructor_inputs=[(datum["adjacency_matrix"],) for datum in data],
        get_solution_mth_name="get_solution",
        expected_solutions=[datum["best_path"] for datum in data],
    )
    tester.add_test(performance_test)
    os.chdir(cwd)

    tester.run()
    print(tester)
    tester.to_file(file_path=f"{root_folder}/test_results.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        input_folder = "./soumissions/RandomTeam"
    else:
        input_folder = sys.argv[1]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        main(input_folder)
