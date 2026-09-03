# Read text for Rabin-Karp
with open("sample.txt", "r") as file:
    text = file.read().strip()

# Get pattern from user
pattern = input("Enter Pattern: ")

print("\nRabin-Karp Result")
print("-----------------")

# Simple Rabin-Karp using Python hash
m = len(pattern)

pattern_hash = hash(pattern)

for i in range(len(text) - m + 1):

    window = text[i:i + m]

    if hash(window) == pattern_hash:

        # Verify actual string to avoid hash collision
        if window == pattern:
            print("Pattern found at index", i)


# Document Similarity

with open("doc1.txt", "r") as file:
    doc1 = file.read().lower().split()

with open("doc2.txt", "r") as file:
    doc2 = file.read().lower().split()


# Find common words
common_words = set(doc1).intersection(set(doc2))

print("\nCommon Words")
print(common_words)


# Calculate similarity
union_words = set(doc1).union(set(doc2))

similarity = (len(common_words) / len(union_words)) * 100

print("Similarity = {:.2f}%".format(similarity))