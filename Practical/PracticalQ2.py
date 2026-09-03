# Open the article repository
with open("Article.txt", "r") as file:
    # Read all articles
    articles = file.readlines()

# Get keyword from user
query = input("Enter keyword: ")

print("\nMatching Articles")
print("---------------------------")

found = False

# Search each article
for article in articles:
    if query.lower() in article.lower():
        print(article.strip())
        found = True

# If no article matches
if not found:
    print("No matching article found.")