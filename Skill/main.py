with open("problem.txt", "r") as file:
    problem = file.readlines()
    print("Computational Problem")
    for problem in problem:
        print(problem.strip())
with open("problem.txt","r") as file:
    problem = file.readlines()
    print("Problem Mapping\n")
    for problem in problem:
        problem = problem.strip()
        print("Problem: ", problem)
        if "search" in problem:
            print("Algorithm: String Matching")

        elif "sort" in problem:
            print("Algorithm: Sorting Algorithm")

        elif "shortest" in problem.lower():
            print("Algorithm: Shortest Path Algorithm")
        elif "duplicate" in problem.lower():
            print("Algorithm: Document Similarity")
        elif "sudoku" in problem:
            print("Algorithm: Backtracking ")
        elif "compress" in problem:
            print("Algorithm: Greedy")
        