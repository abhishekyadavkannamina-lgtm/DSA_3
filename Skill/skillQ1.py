with open("problem.txt", "r") as file:
    problem = file.readlines()
    print("Computational Problem")
    for problem in problem:
        print(problem.strip())
