# Open the article repository
with open("articles.txt", "r") as file:
    # Read all articles from the file
    articles = file.read()

# Display heading
print("TEXTHACK ARTICLE REPOSITORY")
print("----------------------------------")

# Display all articles
print(articles)