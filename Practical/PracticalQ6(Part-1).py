# Sequence Alignment using Dynamic Programming

def sequence_alignment(seq1, seq2):

    # Get lengths
    m = len(seq1)
    n = len(seq2)

    # Create DP table
    dp = [[0 for j in range(n + 1)]
          for i in range(m + 1)]

    # Initialize first column
    for i in range(m + 1):
        dp[i][0] = -i

    # Initialize first row
    for j in range(n + 1):
        dp[0][j] = -j

    # Fill DP table
    for i in range(1, m + 1):

        for j in range(1, n + 1):

            # Match = +1
            # Mismatch = -1
            if seq1[i - 1] == seq2[j - 1]:
                score = 1
            else:
                score = -1

            # Choose maximum score
            dp[i][j] = max(
                dp[i - 1][j - 1] + score,
                dp[i - 1][j] - 1,
                dp[i][j - 1] - 1
            )

    return dp[m][n]


# Input sequences
seq1 = input("Enter Sequence 1: ")
seq2 = input("Enter Sequence 2: ")


# Calculate alignment score
result = sequence_alignment(seq1, seq2)

print("Optimal Alignment Score =", result)