with open("sample.txt", "r") as file:
    text = file.read()
 
# Display the file content
print("----- File Content -----")
print(text)
 
# Ask the user for a search word
word = input("\nEnter the word to search: ")
 
# Search for the word
if word.lower() in text.lower():
    print("\n✅ Word Found")
else:
    print("\n❌ Word Not Found")
